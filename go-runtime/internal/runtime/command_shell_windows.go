//go:build windows

package runtime

import (
    "context"
    "os/exec"
    "strings"
    "syscall"
)

func platformCommandForShell(ctx context.Context, command string) *exec.Cmd {
    cmd:=exec.CommandContext(ctx,"cmd.exe")
    line:=strings.TrimSpace(command)
    if strings.HasPrefix(line,"\"") { line="\""+line+"\"" }
    cmd.SysProcAttr=&syscall.SysProcAttr{CmdLine:"/D /S /C "+line}
    return cmd
}
