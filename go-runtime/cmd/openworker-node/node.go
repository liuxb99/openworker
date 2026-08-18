package main

import (
	"context"
	"errors"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/liuxb99/openworker/go-runtime/internal/api"
	owruntime "github.com/liuxb99/openworker/go-runtime/internal/runtime"
	"github.com/liuxb99/openworker/go-runtime/internal/store"
)

type nodeConfig struct {
	Listen       string
	DataDir      string
	Workers      int
	Capabilities string
}

func normalizeConfig(cfg nodeConfig) (nodeConfig, error) {
	if cfg.Listen == "" { cfg.Listen = "127.0.0.1:8787" }
	if cfg.Workers <= 0 { cfg.Workers = 4 }
	if cfg.DataDir == "" {
		if v := os.Getenv("OPENWORKER_NODE_DATA"); v != "" { cfg.DataDir = v } else { cfg.DataDir = filepath.Join(os.TempDir(), "openworker-node") }
	}
	if cfg.Capabilities == "" { cfg.Capabilities = os.Getenv("OPENWORKER_NODE_CAPABILITIES") }
	if err := os.MkdirAll(cfg.DataDir, 0o755); err != nil { return cfg, err }
	return cfg, nil
}

func runNode(ctx context.Context, cfg nodeConfig) error {
	cfg, err := normalizeConfig(cfg)
	if err != nil { return err }
	if cfg.Capabilities != "" { _ = os.Setenv("OPENWORKER_NODE_CAPABILITIES", cfg.Capabilities) }
	machine, err := os.Hostname()
	if err != nil { return err }
	st, err := store.Open(filepath.Join(cfg.DataDir, "openworker-node.sqlite3"))
	if err != nil { return err }
	defer st.Close()
	rt := owruntime.New(st, cfg.Workers, filepath.Join(cfg.DataDir, "logs"), machine)
	if err := rt.Start(); err != nil { return err }
	defer rt.Stop()

	srv := &http.Server{Addr: cfg.Listen, Handler: api.New(st, rt, machine).Handler(), ReadHeaderTimeout: 5 * time.Second}
	errCh := make(chan error, 1)
	go func() {
		log.Printf("openworker-node machine=%s listen=%s workers=%d data=%s capabilities=%s", machine, cfg.Listen, cfg.Workers, cfg.DataDir, cfg.Capabilities)
		if e := srv.ListenAndServe(); e != nil && !errors.Is(e, http.ErrServerClosed) { errCh <- e; return }
		errCh <- nil
	}()
	select {
	case <-ctx.Done():
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		if err := srv.Shutdown(shutdownCtx); err != nil { return fmt.Errorf("http shutdown: %w", err) }
		return nil
	case err := <-errCh:
		return err
	}
}
