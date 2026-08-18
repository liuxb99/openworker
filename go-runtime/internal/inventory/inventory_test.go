package inventory

import (
	"os"
	"path/filepath"
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

func TestCollectRootsReportsConfiguredExistingDirectories(t *testing.T) {
	tmp:=t.TempDir()
	root:=filepath.Join(tmp,"terrain")
	if err:=os.MkdirAll(root,0o755);err!=nil{t.Fatal(err)}
	old:=os.Getenv("TERRAIN_ROOT")
	defer os.Setenv("TERRAIN_ROOT",old)
	if err:=os.Setenv("TERRAIN_ROOT",root);err!=nil{t.Fatal(err)}

	s:=Collect()
	var got *Root
	for i:=range s.Roots{if s.Roots[i].Env=="TERRAIN_ROOT"{got=&s.Roots[i];break}}
	if got==nil{t.Fatal("TERRAIN_ROOT inventory missing")}
	if !got.Available{t.Fatalf("expected available root: %#v",got)}
	want,err:=filepath.Abs(root);if err!=nil{t.Fatal(err)}
	if got.Path!=filepath.Clean(want){t.Fatalf("path=%q want=%q",got.Path,filepath.Clean(want))}
}

func TestCollectRootsDoesNotClaimMissingDirectoryAvailable(t *testing.T) {
	missing:=filepath.Join(t.TempDir(),"missing")
	old:=os.Getenv("SCENEX_ROOT")
	defer os.Setenv("SCENEX_ROOT",old)
	if err:=os.Setenv("SCENEX_ROOT",missing);err!=nil{t.Fatal(err)}

	s:=Collect()
	for _,root:=range s.Roots{
		if root.Env=="SCENEX_ROOT"{
			if root.Available{t.Fatalf("missing root reported available: %#v",root)}
			return
		}
	}
	t.Fatal("SCENEX_ROOT inventory missing")
}
