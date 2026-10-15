package toolbox

import (
	"context"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/antonikliment/invokr/capability/approval"
	"github.com/antonikliment/invokr/config"
	"github.com/antonikliment/invokr/tools/core"
	"github.com/antonikliment/invokr/tools/core/sandbox"
	"go.uber.org/zap"
)

// Injected using go test -overlay; no file is written into the invokr checkout.
func TestHammerExternalContracts(t *testing.T) {
	root := os.Getenv("HAMMER_TOOLS")
	entries, err := os.ReadDir(root)
	if err != nil || len(entries) == 0 {
		t.Fatalf("HAMMER_TOOLS: %v", err)
	}
	for _, entry := range entries {
		t.Run(entry.Name(), func(t *testing.T) {
			dir := filepath.Join(root, entry.Name())
			cfg := config.ToolboxConfig{}.WithDefaults(t.TempDir())
			if err := ValidateToolDir(dir, cfg); err != nil {
				t.Fatal(err)
			}
			p, err := loadToolboxTool(dir, cfg, zap.NewNop())
			if err != nil {
				t.Fatal(err)
			}
			var call core.ToolCall
			if err := json.Unmarshal([]byte(p.Example), &call); err != nil {
				t.Fatal(err)
			}
			if err := core.ValidateArgs(p.Parameters, call.Arguments); err != nil {
				t.Fatal(err)
			}
			if _, err := os.Stat(filepath.Join(dir, "dependencies.json")); err == nil {
				// Dependency preparation is a separate explicitly online workflow.
				// Python suites use previously prepared pinned environments offline.
				return
			}
			if p.Metadata.Capabilities.Network {
				// Network producers are tested with local mocks by their Python suite.
				// Do not execute an example that could contact a live provider here.
				if len(p.allowHosts) == 0 || p.Metadata.Policy.Approval != "ask" {
					t.Fatal("network manifest lacks allowlist/approval")
				}
				return
			}
			// Exercise the actual Python producer against both Go decoders offline.
			python, err := exec.LookPath("python3")
			if err != nil {
				t.Fatal(err)
			}
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()
			cmd := exec.CommandContext(ctx, python, "-I", "-B", filepath.Join(dir, "main.py"))
			cmd.Env = []string{"PATH=/usr/bin:/bin"}
			cmd.Stdin = strings.NewReader(p.Example)
			raw, err := cmd.Output()
			if err != nil {
				t.Fatal(err)
			}
			for _, decode := range []func(string, string) (string, error){pluginResult, parseDaemonResponse} {
				result, err := decode(p.Name, string(raw))
				if err != nil || !json.Valid([]byte(result)) {
					t.Fatalf("producer/decoder: %q %v", result, err)
				}
			}
			if !sandbox.Available() {
				t.Fatal("namespace sandbox unavailable; containment is required")
			}
			// Copy into private test storage so venv preparation cannot alter the kit.
			staged := t.TempDir()
			for _, name := range []string{"plugin.json", "main.py", "requirements.txt"} {
				data, err := os.ReadFile(filepath.Join(dir, name))
				if err != nil {
					t.Fatal(err)
				}
				if err := os.WriteFile(filepath.Join(staged, name), data, 0600); err != nil {
					t.Fatal(err)
				}
			}
			p, err = loadToolboxTool(staged, cfg, zap.NewNop())
			if err != nil {
				t.Fatal(err)
			}
			// Manual is an approved call, not YOLO; namespace isolation stays enabled.
			ctx, done := approval.NewPolicy(approval.Manual, false).Begin(context.Background(), approval.Request{})
			defer done()
			result, err := p.Invoke(ctx, &call)
			if err != nil || !json.Valid([]byte(result)) {
				t.Fatalf("sandboxed invocation: %q %v", result, err)
			}
		})
	}
}

func TestHammerSiblingContainment(t *testing.T) {
	if !sandbox.Available() {
		t.Fatal("namespace sandbox unavailable")
	}
	python, err := exec.LookPath("python3")
	if err != nil {
		t.Fatal(err)
	}
	toolDir, sibling := t.TempDir(), t.TempDir()
	marker := filepath.Join(sibling, "sentinel")
	if err := os.WriteFile(marker, []byte("intact"), 0600); err != nil {
		t.Fatal(err)
	}
	t.Setenv("HAMMER_FAKE_SECRET", "must-not-inherit")
	netns, err := os.Readlink("/proc/self/ns/net")
	if err != nil {
		t.Fatal(err)
	}
	script := `import os, pathlib, sys
assert 'HAMMER_FAKE_SECRET' not in os.environ
for path in [sys.argv[1], '/etc/passwd', '/proc/1/root' + sys.argv[1]]:
    try: open(path).read()
    except OSError: pass
    else: raise AssertionError('host read escaped: ' + path)
for path in [sys.argv[1], sys.argv[2] + '/mutated']:
    try: open(path, 'w').write('bad')
    except OSError: pass
    else: raise AssertionError('host write escaped: ' + path)
assert os.readlink('/proc/self/ns/net') != sys.argv[3]
assert not pathlib.Path('/tmp/private-scratch').exists()
pathlib.Path('/tmp/private-scratch').write_text('private')
print('contained')`
	plan := sandbox.BuildPlan(python, toolDir, "", "", core.ToolCapabilities{}, 128*1024*1024, nil)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	cmd, cleanup, err := sandbox.Command(ctx, plan, toolDir, []string{"-I", "-B", "-c", script, marker, toolDir, netns})
	if err != nil {
		t.Fatal(err)
	}
	defer cleanup()
	cmd.Env = pluginEnv("python", config.ToolboxConfig{}.WithDefaults(t.TempDir()))
	if out, err := cmd.CombinedOutput(); err != nil || strings.TrimSpace(string(out)) != "contained" {
		t.Fatalf("containment probe: %s %v", out, err)
	}
	if data, err := os.ReadFile(marker); err != nil || string(data) != "intact" {
		t.Fatal("sibling sentinel modified")
	}
}
