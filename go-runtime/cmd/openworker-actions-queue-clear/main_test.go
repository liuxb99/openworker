package main

import "testing"

func TestFirstNonEmpty(t *testing.T) {
    if got := firstNonEmpty("", "  ", "token-a", "token-b"); got != "token-a" {
        t.Fatalf("got %q", got)
    }
    if got := firstNonEmpty("", " "); got != "" {
        t.Fatalf("expected empty, got %q", got)
    }
}
