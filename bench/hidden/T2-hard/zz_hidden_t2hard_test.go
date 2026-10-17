package main

// Hidden acceptance tests for benchmark task T2-hard (versioned store format).
// Black-box: builds the binary and drives it via KV_FILE, so nothing here depends
// on internal APIs. Copied into the repo root only at scoring time.

import (
	"bytes"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"testing"
	"time"
)

var (
	t2hOnce     sync.Once
	t2hBin      string
	t2hBuildErr error
)

func t2hBinary(t *testing.T) string {
	t.Helper()
	t2hOnce.Do(func() {
		dir, err := os.MkdirTemp("", "kvt2hard")
		if err != nil {
			t2hBuildErr = err
			return
		}
		t2hBin = filepath.Join(dir, "kv")
		if out, err := exec.Command("go", "build", "-o", t2hBin, ".").CombinedOutput(); err != nil {
			t2hBuildErr = &t2hBuildError{string(out)}
		}
	})
	if t2hBuildErr != nil {
		t.Fatalf("build failed: %v", t2hBuildErr)
	}
	return t2hBin
}

type t2hBuildError struct{ out string }

func (e *t2hBuildError) Error() string { return e.out }

// t2hRun runs the binary against the store file; returns stdout, stderr, exit code.
func t2hRun(t *testing.T, file string, args ...string) (string, string, int) {
	t.Helper()
	cmd := exec.Command(t2hBinary(t), args...)
	cmd.Env = append(os.Environ(), "KV_FILE="+file)
	var so, se bytes.Buffer
	cmd.Stdout, cmd.Stderr = &so, &se
	code := 0
	if err := cmd.Run(); err != nil {
		ee, ok := err.(*exec.ExitError)
		if !ok {
			t.Fatalf("running %v: %v", args, err)
		}
		code = ee.ExitCode()
	}
	return so.String(), se.String(), code
}

// t2hStore returns a store path inside a fresh directory, with content written when non-empty.
func t2hStore(t *testing.T, content string, mode os.FileMode) string {
	t.Helper()
	p := filepath.Join(t.TempDir(), "store.json")
	if content != "" {
		if err := os.WriteFile(p, []byte(content), mode); err != nil {
			t.Fatal(err)
		}
		if err := os.Chmod(p, mode); err != nil { // defeat umask
			t.Fatal(err)
		}
	}
	return p
}

func t2hNames(t *testing.T, dir string) []string {
	t.Helper()
	es, err := os.ReadDir(dir)
	if err != nil {
		t.Fatal(err)
	}
	var out []string
	for _, e := range es {
		out = append(out, e.Name())
	}
	sort.Strings(out)
	return out
}

// t2hData returns the key/value pairs of a store file and its format version,
// accepting either format the same way the tool is required to.
func t2hData(t *testing.T, path string) (map[string]string, int) {
	t.Helper()
	b, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var top map[string]json.RawMessage
	if err := json.Unmarshal(b, &top); err != nil {
		t.Fatalf("store is not a JSON object: %v (%s)", err, b)
	}
	var version json.Number
	data := map[string]string{}
	if raw, ok := top["version"]; ok && json.Unmarshal(raw, &version) == nil {
		if inner, ok := top["data"]; ok && json.Unmarshal(inner, &data) == nil && version.String() == "2" {
			return data, 2
		}
	}
	data = map[string]string{}
	if err := json.Unmarshal(b, &data); err != nil {
		t.Fatalf("store is neither v2 nor a v1 object: %s", b)
	}
	return data, 1
}

func t2hWant(t *testing.T, got map[string]string, want map[string]string, where string) {
	t.Helper()
	if len(got) != len(want) {
		t.Fatalf("%s: %d keys, want %d (%v)", where, len(got), len(want), got)
	}
	for k, v := range want {
		if got[k] != v {
			t.Fatalf("%s: key %q = %q, want %q (%v)", where, k, got[k], v, got)
		}
	}
}

// --- version command -------------------------------------------------------

func TestT2HVersionOnMissingStore(t *testing.T) {
	p := t2hStore(t, "", 0o644)
	out, errOut, code := t2hRun(t, p, "version")
	if code != 0 {
		t.Fatalf("kv version on a missing store: exit %d, stderr %q", code, errOut)
	}
	if strings.TrimSpace(out) != "2" {
		t.Fatalf("kv version on a missing store printed %q, want 2", out)
	}
	if names := t2hNames(t, filepath.Dir(p)); len(names) != 0 {
		t.Fatalf("kv version created files: %v", names)
	}
}

func TestT2HVersionRejectsArguments(t *testing.T) {
	p := t2hStore(t, `{"a":"1"}`, 0o644)
	if _, _, code := t2hRun(t, p, "version", "x"); code != 2 {
		t.Fatalf("kv version x: exit %d, want 2", code)
	}
}

func TestT2HVersionReportsBothFormats(t *testing.T) {
	v1 := t2hStore(t, `{"a":"1"}`, 0o644)
	if out, _, code := t2hRun(t, v1, "version"); code != 0 || strings.TrimSpace(out) != "1" {
		t.Fatalf("version of a v1 file: %q exit %d, want 1 exit 0", out, code)
	}
	v2 := t2hStore(t, `{"version":2,"data":{"a":"1"}}`, 0o644)
	if out, _, code := t2hRun(t, v2, "version"); code != 0 || strings.TrimSpace(out) != "2" {
		t.Fatalf("version of a v2 file: %q exit %d, want 2 exit 0", out, code)
	}
}

// --- reading must not write ------------------------------------------------

func TestT2HReadingNeverTouchesTheFile(t *testing.T) {
	const orig = `{"b":"2","a":"1"}`
	p := t2hStore(t, orig, 0o644)
	before, err := os.Stat(p)
	if err != nil {
		t.Fatal(err)
	}
	time.Sleep(10 * time.Millisecond)

	if out, _, code := t2hRun(t, p, "get", "a"); code != 0 || strings.TrimSpace(out) != "1" {
		t.Fatalf("get a on a v1 file: %q exit %d", out, code)
	}
	if out, _, code := t2hRun(t, p, "list"); code != 0 || out != "a=1\nb=2\n" {
		t.Fatalf("list on a v1 file: %q exit %d", out, code)
	}
	t2hRun(t, p, "version")
	t2hRun(t, p, "get", "missing")

	b, err := os.ReadFile(p)
	if err != nil {
		t.Fatal(err)
	}
	if string(b) != orig {
		t.Fatalf("a read-only command rewrote the store:\n got %s\nwant %s", b, orig)
	}
	after, err := os.Stat(p)
	if err != nil {
		t.Fatal(err)
	}
	if !after.ModTime().Equal(before.ModTime()) {
		t.Fatalf("a read-only command changed the store's mtime: %v -> %v", before.ModTime(), after.ModTime())
	}
	if names := t2hNames(t, filepath.Dir(p)); len(names) != 1 || names[0] != "store.json" {
		t.Fatalf("a read-only command created files: %v", names)
	}
}

// --- migration -------------------------------------------------------------

func TestT2HFirstWriteMigratesAndKeepsExactBackup(t *testing.T) {
	const orig = `{"b":"2","a":"1"}`
	p := t2hStore(t, orig, 0o644)
	if _, errOut, code := t2hRun(t, p, "set", "c", "3"); code != 0 {
		t.Fatalf("set on a v1 file: exit %d, stderr %q", code, errOut)
	}
	data, version := t2hData(t, p)
	if version != 2 {
		t.Fatalf("after the first write the store is still v1: %v", data)
	}
	t2hWant(t, data, map[string]string{"a": "1", "b": "2", "c": "3"}, "migrated store")

	bak, err := os.ReadFile(p + ".v1.bak")
	if err != nil {
		t.Fatalf("no %s.v1.bak after migration: %v", filepath.Base(p), err)
	}
	if string(bak) != orig {
		t.Fatalf("backup is not the original bytes:\n got %s\nwant %s", bak, orig)
	}
	if names := t2hNames(t, filepath.Dir(p)); len(names) != 2 {
		t.Fatalf("unexpected files after migration: %v", names)
	}
}

func TestT2HNewStoreIsV2WithoutBackup(t *testing.T) {
	p := t2hStore(t, "", 0o644)
	if _, errOut, code := t2hRun(t, p, "set", "a", "1"); code != 0 {
		t.Fatalf("set on a missing store: exit %d, stderr %q", code, errOut)
	}
	data, version := t2hData(t, p)
	if version != 2 {
		t.Fatalf("a new store was not created in v2: %v", data)
	}
	t2hWant(t, data, map[string]string{"a": "1"}, "new store")
	if names := t2hNames(t, filepath.Dir(p)); len(names) != 1 || names[0] != "store.json" {
		t.Fatalf("creating a new store left extra files: %v", names)
	}
}

func TestT2HExistingBackupIsNotOverwritten(t *testing.T) {
	const orig = `{"a":"1"}`
	p := t2hStore(t, orig, 0o644)
	const keep = `{"older":"backup"}`
	if err := os.WriteFile(p+".v1.bak", []byte(keep), 0o644); err != nil {
		t.Fatal(err)
	}
	if _, errOut, code := t2hRun(t, p, "set", "b", "2"); code != 0 {
		t.Fatalf("set with an existing backup: exit %d, stderr %q", code, errOut)
	}
	bak, err := os.ReadFile(p + ".v1.bak")
	if err != nil {
		t.Fatal(err)
	}
	if string(bak) != keep {
		t.Fatalf("an existing .v1.bak was overwritten:\n got %s\nwant %s", bak, keep)
	}
	data, version := t2hData(t, p)
	if version != 2 {
		t.Fatalf("migration did not happen: %v", data)
	}
	t2hWant(t, data, map[string]string{"a": "1", "b": "2"}, "store with pre-existing backup")
}

// The decisive case: a v1 store may contain keys named "version" and "data".
// Detecting v2 by the presence of a "version" field destroys this file.
func TestT2HV1FileWithVersionAndDataKeysSurvives(t *testing.T) {
	const orig = `{"version":"2","data":"hello","a":"1"}`
	p := t2hStore(t, orig, 0o644)

	if out, _, code := t2hRun(t, p, "get", "version"); code != 0 || strings.TrimSpace(out) != "2" {
		t.Fatalf(`get version on a v1 file with a "version" key: %q exit %d, want "2" exit 0`, out, code)
	}
	if out, _, code := t2hRun(t, p, "get", "data"); code != 0 || strings.TrimSpace(out) != "hello" {
		t.Fatalf(`get data on a v1 file with a "data" key: %q exit %d, want "hello" exit 0`, out, code)
	}
	if out, _, code := t2hRun(t, p, "version"); code != 0 || strings.TrimSpace(out) != "1" {
		t.Fatalf("this file is v1; kv version said %q exit %d", out, code)
	}
	if out, _, code := t2hRun(t, p, "list"); code != 0 || out != "a=1\ndata=hello\nversion=2\n" {
		t.Fatalf("list on the ambiguous v1 file: %q exit %d", out, code)
	}
	if _, errOut, code := t2hRun(t, p, "set", "b", "9"); code != 0 {
		t.Fatalf("set on the ambiguous v1 file: exit %d, stderr %q", code, errOut)
	}
	data, version := t2hData(t, p)
	if version != 2 {
		t.Fatalf("the ambiguous file was not migrated to v2: %v", data)
	}
	t2hWant(t, data, map[string]string{"version": "2", "data": "hello", "a": "1", "b": "9"},
		"migrated ambiguous store")
}

func TestT2HMigrationPreservesPermissions(t *testing.T) {
	for _, mode := range []os.FileMode{0o644, 0o640} {
		p := t2hStore(t, `{"a":"1"}`, mode)
		if _, errOut, code := t2hRun(t, p, "set", "b", "2"); code != 0 {
			t.Fatalf("set: exit %d, stderr %q", code, errOut)
		}
		st, err := os.Stat(p)
		if err != nil {
			t.Fatal(err)
		}
		if st.Mode().Perm() != mode {
			t.Fatalf("migration changed permissions: %v, want %v", st.Mode().Perm(), mode)
		}
	}
}

func TestT2HSecondWriteStaysV2WithOneBackup(t *testing.T) {
	p := t2hStore(t, `{"a":"1"}`, 0o644)
	for _, args := range [][]string{{"set", "b", "2"}, {"set", "c", "3"}, {"del", "a"}} {
		if _, errOut, code := t2hRun(t, p, args...); code != 0 {
			t.Fatalf("%v: exit %d, stderr %q", args, code, errOut)
		}
	}
	data, version := t2hData(t, p)
	if version != 2 {
		t.Fatalf("store fell back to v1: %v", data)
	}
	t2hWant(t, data, map[string]string{"b": "2", "c": "3"}, "store after three writes")
	names := t2hNames(t, filepath.Dir(p))
	if len(names) != 2 || names[0] != "store.json" || names[1] != "store.json.v1.bak" {
		t.Fatalf("want exactly the store and one backup, got %v", names)
	}
}

func TestT2HV2RoundTrip(t *testing.T) {
	p := t2hStore(t, "", 0o644)
	cases := map[string]string{
		"plain":   "value",
		"uni":     "日本語 🙂",
		"eq":      "a=b=c",
		"multi":   "line1\nline2",
		"empty":   "",
		"version": "not the format field",
	}
	keys := make([]string, 0, len(cases))
	for k, v := range cases {
		if _, errOut, code := t2hRun(t, p, "set", k, v); code != 0 {
			t.Fatalf("set %q: exit %d, stderr %q", k, code, errOut)
		}
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for k, v := range cases {
		out, errOut, code := t2hRun(t, p, "get", k)
		if code != 0 {
			t.Fatalf("get %q: exit %d, stderr %q", k, code, errOut)
		}
		if out != v+"\n" {
			t.Fatalf("get %q = %q, want %q", k, out, v+"\n")
		}
	}
	if out, _, code := t2hRun(t, p, "version"); code != 0 || strings.TrimSpace(out) != "2" {
		t.Fatalf("version of a tool-written store: %q exit %d", out, code)
	}
	data, version := t2hData(t, p)
	if version != 2 {
		t.Fatalf("tool-written store is not v2: %v", data)
	}
	t2hWant(t, data, cases, "round-tripped store")
}

// --- nothing that worked before may change --------------------------------

func TestT2HExistingBehaviourUnchanged(t *testing.T) {
	// Malformed files stay an error with a message, in either format.
	// Malformed in either format: a value that is not a string, and a file whose
	// numeric `version` is not paired with an object `data` (so it is not v2, and
	// as v1 its number value is invalid).
	for name, content := range map[string]string{
		"invalid json":       `{bad`,
		"v1 number value":    `{"a":1}`,
		"v1 nested value":    `{"a":{"b":"c"}}`,
		"v2 number value":    `{"version":2,"data":{"a":1}}`,
		"v2 data not object": `{"version":2,"data":"x"}`,
	} {
		p := t2hStore(t, content, 0o644)
		if _, errOut, code := t2hRun(t, p, "list"); code != 1 || errOut == "" {
			t.Fatalf("%s: exit %d, stderr %q, want exit 1 with a message", name, code, errOut)
		}
	}

	// All-string "version"/"data" keys are an ordinary v1 store, not a format marker.
	if out, errOut, code := t2hRun(t, t2hStore(t, `{"version":"2","data":"x"}`, 0o644), "list"); code != 0 || errOut != "" || out != "data=x\nversion=2\n" {
		t.Fatalf("v1 file with version/data keys: %q %q exit %d", out, errOut, code)
	}

	// An empty file is an empty store.
	p := t2hStore(t, "", 0o644)
	if err := os.WriteFile(p, nil, 0o644); err != nil {
		t.Fatal(err)
	}
	if out, errOut, code := t2hRun(t, p, "list"); code != 0 || out != "" || errOut != "" {
		t.Fatalf("list on an empty file: %q %q exit %d", out, errOut, code)
	}

	// Commands, output and exit codes.
	q := t2hStore(t, "", 0o644)
	if out, _, code := t2hRun(t, q, "set", "a", "1"); code != 0 || out != "" {
		t.Fatalf("set: %q exit %d", out, code)
	}
	if out, _, code := t2hRun(t, q, "get", "a"); code != 0 || out != "1\n" {
		t.Fatalf("get: %q exit %d", out, code)
	}
	if _, errOut, code := t2hRun(t, q, "get", "nope"); code != 1 || !strings.Contains(errOut, "not found") {
		t.Fatalf("get missing: %q exit %d", errOut, code)
	}
	if _, errOut, code := t2hRun(t, q, "del", "nope"); code != 1 || !strings.Contains(errOut, "not found") {
		t.Fatalf("del missing: %q exit %d", errOut, code)
	}
	if _, _, code := t2hRun(t, q, "del", "a"); code != 0 {
		t.Fatalf("del: exit %d", code)
	}
	if out, _, code := t2hRun(t, q, "list"); code != 0 || out != "" {
		t.Fatalf("list after del: %q exit %d", out, code)
	}
	for _, args := range [][]string{{}, {"set", "a"}, {"get"}, {"foo"}, {"list", "x"}, {"del"}} {
		if _, errOut, code := t2hRun(t, q, args...); code != 2 || errOut == "" {
			t.Fatalf("usage error %v: exit %d, stderr %q, want exit 2", args, code, errOut)
		}
	}
}

func TestT2HNoStrayFilesAfterWrites(t *testing.T) {
	p := t2hStore(t, `{"a":"1"}`, 0o644)
	for i := 0; i < 5; i++ {
		if _, errOut, code := t2hRun(t, p, "set", "k", "v"); code != 0 {
			t.Fatalf("set: exit %d, stderr %q", code, errOut)
		}
	}
	for _, n := range t2hNames(t, filepath.Dir(p)) {
		if strings.Contains(n, ".tmp") || strings.HasPrefix(n, ".kv-") {
			t.Fatalf("temp file left behind: %v", t2hNames(t, filepath.Dir(p)))
		}
	}
}
