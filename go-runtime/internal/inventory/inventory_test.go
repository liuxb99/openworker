package inventory

import (
	"os"
	"testing"
)

func TestCollectCapabilitiesAreNormalized(t *testing.T) {
	old:=os.Getenv("OPENWORKER_NODE_CAPABILITIES")
	defer os.Setenv("OPENWORKER_NODE_CAPABILITIES",old)
	_ = os.Setenv("OPENWORKER_NODE_CAPABILITIES"," blender,case0003,blender, bridge ")
	s:=Collect()
	want:=[]string{"blender","bridge","case0003"}
	if len(s.Capabilities)!=len(want){t.Fatalf("got %#v",s.Capabilities)}
	for i:=range want{if s.Capabilities[i]!=want[i]{t.Fatalf("got %#v want %#v",s.Capabilities,want)}}
	if len(s.Tools)==0{t.Fatal("expected tool inventory")}
}
