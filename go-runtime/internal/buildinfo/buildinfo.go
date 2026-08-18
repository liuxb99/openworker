package buildinfo

var (
	Version = "dev"
	Commit = "unknown"
	BuildTime = "unknown"
)

func Snapshot() map[string]string {
	return map[string]string{
		"version": Version,
		"commit": Commit,
		"build_time": BuildTime,
	}
}
