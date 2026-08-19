package controlcli

import (
    "bytes"
    "os"
    "testing"
)

func TestValidateServerLocalOnly(t *testing.T){
    for _,v:=range[]string{"http://127.0.0.1:8848","http://localhost:8848","http://[::1]:8848"}{if e:=validateServer(v);e!=nil{t.Fatalf("%s: %v",v,e)}}
    for _,v:=range[]string{"https://127.0.0.1:8848","http://DESKTOP-ODAQN0D:8848","http://127.0.0.1:9999","http://127.0.0.1:8848/api"}{if e:=validateServer(v);e==nil{t.Fatalf("expected rejection: %s",v)}}
}
func TestCaseConfigUnknownFailsClosed(t *testing.T){if _,e:=caseConfig("9999");e==nil{t.Fatal("unknown case accepted")}}
func TestMachineAuthority(t *testing.T){h,e:=os.Hostname();if e!=nil{t.Fatal(e)};if e=requireLocalMachine(h);e!=nil{t.Fatal(e)};if e=requireLocalMachine(h+"-WRONG");e==nil{t.Fatal("wrong host accepted")}}
func TestUsageDoesNotRequirePython(t *testing.T){var out,err bytes.Buffer;code:=Run("openworker",[]string{"case","status"},&out,&err);if code!=2{t.Fatalf("code=%d",code)};if bytes.Contains(err.Bytes(),[]byte("python")){t.Fatalf("usage leaked Python dependency: %s",err.String())}}
