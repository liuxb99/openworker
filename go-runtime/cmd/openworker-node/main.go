package main

import (
	"context"
	"flag"
	"log"
	"os"
	"os/signal"
	"syscall"
)

func main() {
	var cfg nodeConfig
	var serviceMode bool
	flag.StringVar(&cfg.Listen, "listen", "127.0.0.1:8787", "listen address")
	flag.StringVar(&cfg.DataDir, "data", "", "durable data directory")
	flag.IntVar(&cfg.Workers, "workers", 4, "max concurrent workers")
	flag.StringVar(&cfg.Capabilities, "capabilities", "", "comma-separated node capabilities")
	flag.BoolVar(&serviceMode, "service", false, "run under the native Windows Service Control Manager")
	flag.Parse()

	if serviceMode {
		if err := runWindowsService(cfg); err != nil { log.Fatal(err) }
		return
	}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	if err := runNode(ctx, cfg); err != nil { log.Fatal(err) }
}
