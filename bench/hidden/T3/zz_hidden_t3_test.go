package main

// Hid3 acceptance tests for benchmark task T3 (kv-bugs: ordering, permissions, lost updates).
// Black-box: builds the binary and drives it, so it does not depend on internal APIs.
// Copied into the repo root only at scoring time.

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"sort"
	"strings"
	"sync"
	"testing"
)

var (
	hid3BuildOnce sync.Once
	hid3Bin       string
	hid3BuildErr  error
)

func hid3Binary(t *testing.T) string {
	t.Helper()
	hid3BuildOnce.Do(func() {
		dir, err := os.MkdirTemp("", "kvhid3")
		if err != nil {
			hid3BuildErr = err
			return
		}
		hid3Bin = filepath.Join(dir, "kv")
		out, err := exec.Command("go", "build", "-o", hid3Bin, ".").CombinedOutput()
		if err != nil {
			hid3BuildErr = &hid3BuildError{string(out)}
		}
	})
	if hid3BuildErr != nil {
		t.Fatalf("build failed: %v", hid3BuildErr)
	}
	return hid3Bin
}

type hid3BuildError struct{ out string }

func (e *hid3BuildError) Error() string { return e.out }

// kv runs the binary against file; returns stdout, stderr, exit code.
func hid3Kv(t *testing.T, file string, args ...string) (string, string, int) {
	t.Helper()
	cmd := exec.Command(hid3Binary(t), args...)
	cmd.Env = append(os.Environ(), "KV_FILE="+file)
	var so, se bytes.Buffer
	cmd.Stdout, cmd.Stderr = &so, &se
	err := cmd.Run()
	code := 0
	if err != nil {
		ee, ok := err.(*exec.ExitError)
		if !ok {
			t.Fatalf("run: %v", err)
		}
		code = ee.ExitCode()
	}
	return so.String(), se.String(), code
}

func hid3KeysOf(t *testing.T, file string) []string {
	t.Helper()
	out, _, code := hid3Kv(t, file, "list")
	if code != 0 {
		t.Fatalf("list exit %d", code)
	}
	var ks []string
	for _, l := range strings.Split(strings.TrimSpace(out), "\n") {
		if l != "" {
			ks = append(ks, strings.SplitN(l, "=", 2)[0])
		}
	}
	return ks
}

func TestT3ListIsBytewiseSorted(t *testing.T) {
	f := filepath.Join(t.TempDir(), "kv.json")
	for _, k := range []string{"b", "aa", "a", "B", "ab", "zz", "10", "9"} {
		if _, _, c := hid3Kv(t, f, "set", k, "v"); c != 0 {
			t.Fatalf("set %s failed", k)
		}
	}
	got := hid3KeysOf(t, f)
	want := append([]string(nil), got...)
	sort.Strings(want)
	if !reflect.DeepEqual(got, want) || len(got) != 8 {
		t.Fatalf("list order %v, want %v", got, want)
	}
}

func TestT3PermissionsPreserved(t *testing.T) {
	for _, mode := range []os.FileMode{0o644, 0o640, 0o600} {
		f := filepath.Join(t.TempDir(), "kv.json")
		if err := os.WriteFile(f, []byte(`{"a":"1"}`), mode); err != nil {
			t.Fatal(err)
		}
		os.Chmod(f, mode)
		if _, _, c := hid3Kv(t, f, "set", "b", "2"); c != 0 {
			t.Fatal("set failed")
		}
		if st, _ := os.Stat(f); st.Mode().Perm() != mode {
			t.Fatalf("after set mode=%v want %v", st.Mode().Perm(), mode)
		}
		if _, _, c := hid3Kv(t, f, "del", "a"); c != 0 {
			t.Fatal("del failed")
		}
		if st, _ := os.Stat(f); st.Mode().Perm() != mode {
			t.Fatalf("after del mode=%v want %v", st.Mode().Perm(), mode)
		}
	}
}

func hid3Parallel(t *testing.T, n int, fn func(i int) (int, string)) {
	t.Helper()
	var wg sync.WaitGroup
	errs := make(chan string, n)
	start := make(chan struct{})
	for i := 0; i < n; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			<-start
			if c, e := fn(i); c != 0 {
				errs <- fmt.Sprintf("worker %d exit %d: %s", i, c, e)
			}
		}(i)
	}
	close(start)
	wg.Wait()
	close(errs)
	for e := range errs {
		t.Error(e)
	}
}

func TestT3ConcurrentSetsLoseNothing(t *testing.T) {
	for round := 0; round < 3; round++ {
		f := filepath.Join(t.TempDir(), "kv.json")
		const n = 40
		hid3Parallel(t, n, func(i int) (int, string) {
			_, e, c := hid3Kv(t, f, "set", fmt.Sprintf("k%02d", i), "v")
			return c, e
		})
		if got := hid3KeysOf(t, f); len(got) != n {
			t.Fatalf("round %d: %d keys survived, want %d", round, len(got), n)
		}
	}
}

func TestT3ConcurrentSetAndDelete(t *testing.T) {
	for round := 0; round < 3; round++ {
		d := t.TempDir()
		f := filepath.Join(d, "kv.json")
		const n = 25
		m := map[string]string{}
		for i := 0; i < n; i++ {
			m[fmt.Sprintf("d%02d", i)] = "old"
		}
		b, _ := json.Marshal(m)
		os.WriteFile(f, b, 0o644)
		hid3Parallel(t, 2*n, func(i int) (int, string) {
			var e string
			var c int
			if i < n {
				_, e, c = hid3Kv(t, f, "set", fmt.Sprintf("s%02d", i), "new")
			} else {
				_, e, c = hid3Kv(t, f, "del", fmt.Sprintf("d%02d", i-n))
			}
			return c, e
		})
		got := hid3KeysOf(t, f)
		if len(got) != n {
			t.Fatalf("round %d: keys=%v, want exactly s00..s24", round, got)
		}
		for _, k := range got {
			if !strings.HasPrefix(k, "s") {
				t.Fatalf("round %d: stale key %s survived: %v", round, k, got)
			}
		}
		es, _ := os.ReadDir(d)
		for _, e := range es {
			if strings.HasSuffix(e.Name(), ".tmp") {
				t.Fatalf("temp file left behind: %s", e.Name())
			}
		}
	}
}

func TestT3ConcurrentSameKeyEndsConsistent(t *testing.T) {
	f := filepath.Join(t.TempDir(), "kv.json")
	hid3Parallel(t, 30, func(i int) (int, string) {
		_, e, c := hid3Kv(t, f, "set", "same", fmt.Sprintf("v%d", i))
		return c, e
	})
	out, _, c := hid3Kv(t, f, "get", "same")
	if c != 0 || !strings.HasPrefix(out, "v") {
		t.Fatalf("get same: %d %q", c, out)
	}
}

func TestT3ExistingBehaviourUnchanged(t *testing.T) {
	f := filepath.Join(t.TempDir(), "kv.json")
	if _, _, c := hid3Kv(t, f, "set", "a", "1"); c != 0 {
		t.Fatal("set")
	}
	if out, _, c := hid3Kv(t, f, "get", "a"); c != 0 || out != "1\n" {
		t.Fatalf("get %d %q", c, out)
	}
	if _, e, c := hid3Kv(t, f, "get", "nope"); c != 1 || e == "" {
		t.Fatalf("get missing %d %q", c, e)
	}
	if _, e, c := hid3Kv(t, f, "del", "nope"); c != 1 || e == "" {
		t.Fatalf("del missing %d %q", c, e)
	}
	if _, _, c := hid3Kv(t, f); c != 2 {
		t.Fatalf("no args exit %d want 2", c)
	}
	if _, _, c := hid3Kv(t, f, "bogus"); c != 2 {
		t.Fatalf("unknown cmd exit %d want 2", c)
	}
	if _, _, c := hid3Kv(t, f, "set", "only-key"); c != 2 {
		t.Fatalf("wrong arity exit %d want 2", c)
	}
	os.WriteFile(f, []byte("{nope"), 0o644)
	if _, _, c := hid3Kv(t, f, "list"); c != 1 {
		t.Fatalf("corrupt store exit %d want 1", c)
	}
}
