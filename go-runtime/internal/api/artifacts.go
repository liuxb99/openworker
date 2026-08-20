package api

import (
    "crypto/sha256"
    "encoding/hex"
    "io"
    "io/fs"
    "net/http"
    "os"
    "path/filepath"
    "sort"
    "strconv"
    "strings"
    "time"

    "github.com/liuxb99/openworker/go-runtime/internal/model"
)

type jobArtifact struct {
    Path             string    `json:"path"`
    RelativePath     string    `json:"relative_path,omitempty"`
    Kind             string    `json:"kind"`
    Size             int64     `json:"size"`
    SHA256           string    `json:"sha256,omitempty"`
    ModifiedAt       time.Time `json:"modified_at"`
    DuringJobWindow  bool      `json:"during_job_window"`
}

type slotSnapshot struct {
    Slot       int         `json:"slot"`
    Current    *model.Job  `json:"current,omitempty"`
    History    []model.Job `json:"history"`
    Total      int         `json:"total"`
    Succeeded  int         `json:"succeeded"`
    Failed     int         `json:"failed"`
}

func (s *Server) slots(w http.ResponseWriter, r *http.Request) {
    jobs, err := s.store.List(queryInt(r, "limit", 500))
    if err != nil { writeErr(w, 500, err); return }
    bySlot := map[int][]model.Job{}
    maxSlot := 0
    for _, j := range jobs {
        if j.AgentSlot <= 0 { continue }
        bySlot[j.AgentSlot] = append(bySlot[j.AgentSlot], j)
        if j.AgentSlot > maxSlot { maxSlot = j.AgentSlot }
    }
    if maxSlot < 4 { maxSlot = 4 }
    out := make([]slotSnapshot, 0, maxSlot)
    for slot := 1; slot <= maxSlot; slot++ {
        hist := bySlot[slot]
        sort.SliceStable(hist, func(i, k int) bool { return hist[i].CreatedAt.After(hist[k].CreatedAt) })
        snap := slotSnapshot{Slot: slot, History: hist, Total: len(hist)}
        for i := range hist {
            switch hist[i].Status {
            case model.StatusRunning, model.StatusStarting:
                if snap.Current == nil { x := hist[i]; snap.Current = &x }
            case model.StatusSucceeded:
                snap.Succeeded++
            case model.StatusFailed, model.StatusTimedOut, model.StatusCancelled:
                snap.Failed++
            }
        }
        out = append(out, snap)
    }
    writeJSON(w, 200, map[string]any{"slots": out, "count": len(out)})
}

func (s *Server) artifacts(w http.ResponseWriter, r *http.Request) {
    job, err := s.store.Get(r.PathValue("jobID"))
    if err != nil { writeErr(w, 404, err); return }
    rows := make([]jobArtifact, 0, 32)
    addFile := func(path, kind, rel string) {
        st, e := os.Stat(path); if e != nil || !st.Mode().IsRegular() { return }
        start := job.CreatedAt.Add(-2*time.Minute)
        end := time.Now().UTC().Add(2*time.Minute)
        if job.FinishedAt != nil { end = job.FinishedAt.Add(2*time.Minute) }
        during := !st.ModTime().Before(start) && !st.ModTime().After(end)
        row := jobArtifact{Path:path, RelativePath:rel, Kind:kind, Size:st.Size(), ModifiedAt:st.ModTime().UTC(), DuringJobWindow:during}
        if st.Size() <= 512<<20 {
            if f, e := os.Open(path); e == nil { h:=sha256.New(); if _,e=io.Copy(h,f); e==nil { row.SHA256=hex.EncodeToString(h.Sum(nil)) }; _=f.Close() }
        }
        rows = append(rows, row)
    }
    if job.StdoutPath != "" { addFile(job.StdoutPath, "stdout", filepath.Base(job.StdoutPath)) }
    if job.StderrPath != "" { addFile(job.StderrPath, "stderr", filepath.Base(job.StderrPath)) }

    root := strings.TrimSpace(job.WorkspaceRoot)
    roots := []string{"presentation","artifacts","artifact","output","outputs","evidence","deliverables","renders","results","reports"}
    limit := queryInt(r,"limit",200); if limit < 1 { limit=1 }; if limit > 500 { limit=500 }
    if root != "" {
        for _, name := range roots {
            base := filepath.Join(root,name)
            st,e:=os.Stat(base); if e!=nil || !st.IsDir(){continue}
            _ = filepath.WalkDir(base, func(path string, d fs.DirEntry, walkErr error) error {
                if walkErr != nil { return nil }
                if len(rows) >= limit { return fs.SkipAll }
                if d.IsDir() { return nil }
                rel,e:=filepath.Rel(root,path); if e!=nil { rel=filepath.Base(path) }
                addFile(path,"workspace_artifact",rel)
                return nil
            })
            if len(rows)>=limit { break }
        }
    }
    sort.SliceStable(rows, func(i,j int) bool {
        if rows[i].DuringJobWindow != rows[j].DuringJobWindow { return rows[i].DuringJobWindow }
        return rows[i].ModifiedAt.After(rows[j].ModifiedAt)
    })
    writeJSON(w,200,map[string]any{"job_id":job.JobID,"slot":job.AgentSlot,"workspace_root":job.WorkspaceRoot,"artifacts":rows,"count":len(rows),"hash_limit_bytes":512<<20,"scan_limit":limit,"window_start":job.CreatedAt.Add(-2*time.Minute),"window_end":artifactWindowEnd(job)})
}

func artifactWindowEnd(job model.Job) time.Time {
    if job.FinishedAt != nil { return job.FinishedAt.Add(2*time.Minute) }
    return time.Now().UTC().Add(2*time.Minute)
}

var _ = strconv.Itoa
