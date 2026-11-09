// ItsOcho Studio - transparent Windows launcher.
// Source is supplied so recipients can verify what the EXE does.
// This launcher does not install software, request administrator privileges,
// modify the registry, contact an external website or run a remote command.
// It starts the included Python localhost server and leaves this console open.
package main

import (
    "bufio"
    "context"
    "fmt"
    "os"
    "os/exec"
    "path/filepath"
    "runtime"
    "strings"
    "time"
)

type pythonCandidate struct { command string; prefix []string }

func probe(p pythonCandidate) bool {
    ctx, cancel := context.WithTimeout(context.Background(), 4*time.Second)
    defer cancel()
    argv := append(append([]string{}, p.prefix...), "-c", "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)")
    cmd := exec.CommandContext(ctx, p.command, argv...)
    cmd.Stdin = nil
    return cmd.Run() == nil
}

func findPython(base string) (pythonCandidate, bool) {
    candidates := make([]pythonCandidate, 0, 32)
    add := func(path string, prefix ...string) {
        if strings.TrimSpace(path) != "" {
            candidates = append(candidates, pythonCandidate{path, prefix})
        }
    }
    if buf, err := os.ReadFile(filepath.Join(base, "RUTA_PYTHON.txt")); err == nil {
        add(strings.Trim(strings.TrimSpace(string(buf)), "\""))
    }
    add(os.Getenv("ITSOCHO_PYTHON"))
    local := os.Getenv("LOCALAPPDATA")
    program := os.Getenv("ProgramFiles")
    home := os.Getenv("USERPROFILE")
    for _, v := range []string{"315", "314", "313", "312", "311", "310"} {
        add(filepath.Join(local, "Programs", "Python", "Python"+v, "python.exe"))
        add(filepath.Join(program, "Python"+v, "python.exe"))
    }
    add(filepath.Join(home, "scoop", "apps", "python", "current", "python.exe"))
    add("py", "-3")
    add("python")
    add("python3")
    for _, p := range candidates {
        if probe(p) {return p, true}
    }
    return pythonCandidate{}, false
}

func waitForEnter() {
    fmt.Println("\nPulsa Enter para cerrar esta ventana.")
    _, _ = bufio.NewReader(os.Stdin).ReadString('\n')
}

func main() {
    exe, err := os.Executable()
    if err != nil {
        fmt.Println("No se pudo encontrar la ruta del programa:", err)
        waitForEnter()
        os.Exit(1)
    }
    base := filepath.Dir(exe)
    fmt.Println("=======================================================")
    fmt.Println(" ITSOCHO STUDIO  |  LANZADOR LOCAL PARA WINDOWS")
    fmt.Println("=======================================================")
    fmt.Println("Panel:   http://127.0.0.1:8767/panel")
    fmt.Println("Overlay: http://127.0.0.1:8767/overlay")
    fmt.Println("Musica:  http://127.0.0.1:8767/music")
    fmt.Println("No solicita permisos de administrador.")
    fmt.Println("Cierra esta ventana para detener el servidor.")
    fmt.Println("-------------------------------------------------------")
    if runtime.GOOS != "windows" {
        fmt.Println("Este ejecutable esta disenado para Windows.")
        waitForEnter()
        return
    }
    for _, name := range []string{"server.py", "panel.html", "overlay.html", "music.html"} {
        if st, e := os.Stat(filepath.Join(base, name)); e != nil || st.IsDir() {
            fmt.Printf("ERROR: Falta %s en la carpeta del programa.\nExtrae el ZIP completo.\n", name)
            waitForEnter()
            return
        }
    }
    py, ok := findPython(base)
    if !ok {
        fmt.Println("No se encontro Python 3.10 o superior.")
        fmt.Println("Puedes usar INICIAR_PANEL.bat para diagnosticar el problema.")
        fmt.Println("Para compartir sin Python, ejecuta COMPILAR_EXE_AUTONOMO.bat en tu PC.")
        waitForEnter()
        return
    }
    fmt.Printf("Python encontrado: %s\n", py.command)
    fmt.Println("Iniciando servidor local. La ventana permanecera abierta...")
    args := append(append([]string{}, py.prefix...), "-u", filepath.Join(base, "server.py"))
    child := exec.Command(py.command, args...)
    child.Dir = base
    child.Stdout = os.Stdout
    child.Stderr = os.Stderr
    child.Stdin = os.Stdin
    // Let Python open the browser and serve OBS, as it already does in the BAT.
    if e := child.Run(); e != nil {
        fmt.Println("\nEl panel se ha detenido:", e)
        waitForEnter()
    }
}
