package main

// Hidden acceptance tests for benchmark task T2 (kv export / kv import).
// Black-box: builds the binary and drives it, so it does not depend on internal APIs.
// Copied into the repo root only at scoring time.

import (
	"bytes"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"strings"
	"sync"
	"testing"
)

var (
	hiddenBuildOnce sync.Once
	hiddenBin       string
	hiddenBuildErr  error
)

func hiddenBinary(t *testing.T) string {
	t.Helper()
	hiddenBuildOnce.Do(func() {
		dir, err := os.MkdirTemp("", "kvhidden")
		if err != nil {
			hiddenBuildErr = err
			return
		}
		hiddenBin = filepath.Join(dir, "kv")
		out, err := exec.Command("go", "build", "-o", hiddenBin, ".").CombinedOutput()
		if err != nil {
			hiddenBuildErr = &buildError{string(out)}
		}
	})
	if hiddenBuildErr != nil {
		t.Fatalf("build failed: %v", hiddenBuildErr)
	}
	return hiddenBin
}

type buildError struct{ out string }

func (e *buildError) Error() string { return e.out }

// kv runs the binary against file with optional stdin; returns stdout, stderr, exit code.
func kv(t *testing.T, file, stdin string, args ...string) (string, string, int) {
	t.Helper()
	cmd := exec.Command(hiddenBinary(t), args...)
	cmd.Env = append(os.Environ(), "KV_FILE="+file)
	cmd.Stdin = strings.NewReader(stdin)
	var so, se bytes.Buffer
	cmd.Stdout, cmd.Stderr = &so, &se
	err := cmd.Run()
	code := 0
	if err != nil {
		ee, ok := err.(*exec.ExitError)
		if !ok {
			t.Fatalf("run %v: %v", args, err)
		}
		code = ee.ExitCode()
	}
	return so.String(), se.String(), code
}

func newStore(t *testing.T, pairs ...string) string {
	t.Helper()
	f := filepath.Join(t.TempDir(), "kv.json")
	for i := 0; i+1 < len(pairs); i += 2 {
		if _, se, c := kv(t, f, "", "set", pairs[i], pairs[i+1]); c != 0 {
			t.Fatalf("seed set %s: exit %d %s", pairs[i], c, se)
		}
	}
	return f
}

func listOf(t *testing.T, f string) string {
	t.Helper()
	out, _, c := kv(t, f, "", "list")
	if c != 0 {
		t.Fatalf("list exit %d", c)
	}
	return out
}

func TestHiddenExportEmpty(t *testing.T) {
	f := newStore(t)
	out, _, c := kv(t, f, "", "export")
	if c != 0 {
		t.Fatalf("exit %d", c)
	}
	if strings.TrimSpace(out) != "{}" {
		t.Fatalf("want {}, got %q", out)
	}
}

func TestHiddenExportContentAndSortedKeys(t *testing.T) {
	f := newStore(t, "zeta", "26", "alpha", "1", "mid", "13")
	out, se, c := kv(t, f, "", "export")
	if c != 0 || se != "" {
		t.Fatalf("exit %d stderr %q", c, se)
	}
	var got map[string]string
	if err := json.Unmarshal([]byte(out), &got); err != nil {
		t.Fatalf("stdout is not one JSON object: %v\n%s", err, out)
	}
	want := map[string]string{"zeta": "26", "alpha": "1", "mid": "13"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %v want %v", got, want)
	}
	ia, im, iz := strings.Index(out, `"alpha"`), strings.Index(out, `"mid"`), strings.Index(out, `"zeta"`)
	if !(ia >= 0 && ia < im && im < iz) {
		t.Fatalf("keys not sorted in output: %s", out)
	}
}

func TestHiddenExportSpecialCharsRoundTrip(t *testing.T) {
	f := newStore(t, `quo"te`, `va"lue`, "uni", "héllo 世界", "nl", "line1\nline2")
	out, _, c := kv(t, f, "", "export")
	if c != 0 {
		t.Fatalf("exit %d", c)
	}
	g := newStore(t)
	if _, se, c := kv(t, g, out, "import"); c != 0 {
		t.Fatalf("import exit %d %s", c, se)
	}
	if listOf(t, f) != listOf(t, g) {
		t.Fatalf("round trip differs:\n%q\n%q", listOf(t, f), listOf(t, g))
	}
}

func TestHiddenImportMergesAndOverwrites(t *testing.T) {
	f := newStore(t, "a", "1", "b", "2")
	so, se, c := kv(t, f, `{"b":"9","c":"3"}`, "import")
	if c != 0 {
		t.Fatalf("exit %d %s %s", c, so, se)
	}
	if got := listOf(t, f); got != "a=1\nb=9\nc=3\n" {
		t.Fatalf("got %q", got)
	}
}

func TestHiddenImportEmptyObjectIsNoOp(t *testing.T) {
	f := newStore(t, "a", "1")
	if _, se, c := kv(t, f, `{}`, "import"); c != 0 {
		t.Fatalf("exit %d %s", c, se)
	}
	if got := listOf(t, f); got != "a=1\n" {
		t.Fatalf("got %q", got)
	}
}

func TestHiddenImportRejectsBadInputAtomically(t *testing.T) {
	cases := map[string]string{
		"invalid json":     `{"a":`,
		"not an object":    `["a","b"]`,
		"number value":     `{"x":"1","y":2}`,
		"null value":       `{"x":"1","y":null}`,
		"nested value":     `{"x":"1","y":{"z":"1"}}`,
		"empty stdin":      ``,
		"trailing garbage": `{"x":"1"} nope`,
	}
	for name, input := range cases {
		t.Run(name, func(t *testing.T) {
			f := newStore(t, "keep", "me")
			so, se, c := kv(t, f, input, "import")
			if c != 1 {
				t.Fatalf("exit %d, want 1", c)
			}
			if so != "" || strings.TrimSpace(se) == "" {
				t.Fatalf("stdout %q stderr %q", so, se)
			}
			if got := listOf(t, f); got != "keep=me\n" {
				t.Fatalf("store changed: %q", got)
			}
		})
	}
}

func TestHiddenExistingBehaviorUnchanged(t *testing.T) {
	f := newStore(t)
	if so, _, c := kv(t, f, "", "list"); c != 0 || so != "" {
		t.Fatalf("empty list: exit %d out %q", c, so)
	}
	kv(t, f, "", "set", "b", "2")
	kv(t, f, "", "set", "a", "1")
	if got := listOf(t, f); got != "a=1\nb=2\n" {
		t.Fatalf("list %q", got)
	}
	if so, _, c := kv(t, f, "", "get", "a"); c != 0 || so != "1\n" {
		t.Fatalf("get: %d %q", c, so)
	}
	if _, se, c := kv(t, f, "", "get", "zz"); c != 1 || se == "" {
		t.Fatalf("get missing: %d %q", c, se)
	}
	if _, _, c := kv(t, f, "", "del", "zz"); c != 1 {
		t.Fatalf("del missing: %d", c)
	}
	if _, _, c := kv(t, f, "", "del", "a"); c != 0 {
		t.Fatalf("del: %d", c)
	}
	if _, _, c := kv(t, f, "", "bogus"); c != 2 {
		t.Fatalf("unknown cmd: %d", c)
	}
	if _, _, c := kv(t, f, "", "set", "onlykey"); c != 2 {
		t.Fatalf("missing arg: %d", c)
	}
}
