package main

import (
    "os"
    "testing"
)

func TestValidateServerLocalOnly(t *testing.T) {
    for _, good := range []string{"http://127.0.0.1:8848", "http://localhost:8848", "http://[::1]:8848"} {
        if err := validateServer(good); err != nil { t.Fatalf("%s: %v", good, err) }
    }
    for _, bad := range []string{"https://127.0.0.1:8848", "http://DESKTOP-ODAQN0D:8848", "http://127.0.0.1:9999", "http://127.0.0.1:8848/api"} {
        if err := validateServer(bad); err == nil { t.Fatalf("expected rejection for %s", bad) }
    }
}

func TestCaseConfigFailsClosedForUnknownCase(t *testing.T) {
    if _, err := caseConfig("9999"); err == nil { t.Fatal("unknown case must fail closed") }
}

func TestRequireLocalMachineRejectsWrongHost(t *testing.T) {
    host, err := os.Hostname(); if err != nil { t.Fatal(err) }
    if err := requireLocalMachine(host); err != nil { t.Fatalf("local host rejected: %v", err) }
    if err := requireLocalMachine(host + "-WRONG"); err == nil { t.Fatal("wrong machine must be rejected") }
}
