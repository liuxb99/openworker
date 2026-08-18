package cluster

import(
 "context"
 "net/http"
 "strings"
 "sync"
 "time"
)

type Controller struct{registry *Registry;client *http.Client;endpoints []string;interval time.Duration;mu sync.Mutex;stop context.CancelFunc}
func NewController(endpoints []string)*Controller{clean:=[]string{};seen:=map[string]bool{};for _,e:=range endpoints{e=strings.TrimSpace(e);if e!=""&&!seen[e]{seen[e]=true;clean=append(clean,e)}};return &Controller{registry:NewRegistry(),client:&http.Client{Timeout:3*time.Second},endpoints:clean,interval:5*time.Second}}
func(c *Controller)Registry()*Registry{return c.registry}
func(c *Controller)Start(parent context.Context){c.mu.Lock();defer c.mu.Unlock();if c.stop!=nil{return};ctx,cancel:=context.WithCancel(parent);c.stop=cancel;c.probeAll();go func(){t:=time.NewTicker(c.interval);defer t.Stop();for{select{case<-ctx.Done():return;case<-t.C:c.probeAll()}}}()}
func(c *Controller)Stop(){c.mu.Lock();if c.stop!=nil{c.stop();c.stop=nil};c.mu.Unlock()}
func(c *Controller)probeAll(){for _,e:=range c.endpoints{n,err:=Probe(c.client,e);if err!=nil{oldID:=key(e);for _,old:=range c.registry.Nodes(){if old.Endpoint==e{oldID=old.NodeID;n=old;break}};n.NodeID=oldID;n.Endpoint=e;n.Online=false;n.LastError=err.Error();n.LeaseUntil=time.Now().UTC();c.registry.Upsert(n);continue};c.registry.Upsert(n)}}
func(c *Controller)Status()map[string]any{nodes:=c.registry.Nodes();online:=0;for _,n:=range nodes{if n.Online{online++}};return map[string]any{"nodes":nodes,"node_count":len(nodes),"online_count":online,"offline_count":len(nodes)-online,"observed_at":time.Now().UTC()}}
func(c *Controller)Capabilities()map[string]any{out:=map[string][]string{};for _,n:=range c.registry.Nodes(){out[n.NodeID]=n.Capabilities};return map[string]any{"capabilities":out,"observed_at":time.Now().UTC()}}
