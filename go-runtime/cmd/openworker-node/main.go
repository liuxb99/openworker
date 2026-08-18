package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	"github.com/liuxb99/openworker/go-runtime/internal/api"
	owruntime "github.com/liuxb99/openworker/go-runtime/internal/runtime"
	"github.com/liuxb99/openworker/go-runtime/internal/store"
)

func main(){
	var listen,dataDir string
	var workers int
	flag.StringVar(&listen,"listen","127.0.0.1:8787","listen address")
	flag.StringVar(&dataDir,"data","","durable data directory")
	flag.IntVar(&workers,"workers",4,"max concurrent workers")
	flag.Parse()

	machine,err:=os.Hostname();if err!=nil{log.Fatal(err)}
	if dataDir==""{if v:=os.Getenv("OPENWORKER_NODE_DATA");v!=""{dataDir=v}else{dataDir=filepath.Join(os.TempDir(),"openworker-node")}}
	if err:=os.MkdirAll(dataDir,0o755);err!=nil{log.Fatal(err)}

	st,err:=store.Open(filepath.Join(dataDir,"openworker-node.sqlite3"));if err!=nil{log.Fatal(err)};defer st.Close()
	rt:=owruntime.New(st,workers,filepath.Join(dataDir,"logs"),machine);if err:=rt.Start();err!=nil{log.Fatal(err)};defer rt.Stop()

	srv:=&http.Server{Addr:listen,Handler:api.New(st,rt,machine).Handler(),ReadHeaderTimeout:5*time.Second}
	go func(){log.Printf("openworker-node machine=%s listen=%s workers=%d data=%s",machine,listen,workers,dataDir);if err:=srv.ListenAndServe();err!=nil&&err!=http.ErrServerClosed{log.Fatal(err)}}()

	sig:=make(chan os.Signal,1);signal.Notify(sig,os.Interrupt,syscall.SIGTERM);<-sig
	fmt.Println("openworker-node shutting down")
}
