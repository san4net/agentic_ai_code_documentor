# cp-master

## Overview
cp-master is a Java-based desktop application designed for managing file copy and paste tasks with a graphical user interface. It utilizes Java Swing components, concurrent task execution, and memory-mapped file operations.

## Languages
- **Primary Language**: Java (15 source/test files)

## Directory Layout
- `pom.xml`: Project build and configuration manifest.
- `src/main/java/com/copypaste/`: Core application interfaces and UI classes.
  - `adapter/`: Adapters for concurrent task execution (`CallableAdapter`).
  - `impls/`: Implementations of copy-paste logic, tasks, and UI (`CopyPasteTask`, `CopyPasteUIImpl`, `MemoryMappedCopyPasteImpl`).
  - `logic/`: Business logic definitions (`CopyPasteLogic`).
  - `run/`: Application entry point (`CPMain`).
  - `util/`: Helper utilities and constants (`Constants`, `GenericUtil`, `StringSupport`, `Utils`).
- `src/main/resources/script/`: Resource scripts (if any).
- `src/test/java/com/copypaste/`: Test classes (`CopyPasteTest`).

## Important Modules & Components
- **Entry Point**: `com.copypaste.run.CPMain` launches the application UI.
- **UI Implementation**: `com.copypaste.impls.CopyPasteUIImpl` provides the Java Swing-based interface, task status monitoring, serialization, and background worker processing.
- **Copy/Paste Logic & Implementations**:
  - `com.copypaste.logic.CopyPasteLogic`: Interface for copy-paste operations.
  - `com.copypaste.impls.MemoryMappedCopyPasteImpl`: Implements file copy operations utilizing memory-mapped buffers (`FileChannel`, `ByteBuffer`).
  - `com.copypaste.impls.CopyPasteTask`: Manages asynchronous directory and file copy tasks using executor services.
- **Historical & UI Components**: `HistoricalCombo`, `HistoricalJList`, and `CopyPasteUI` handle user interaction states and past operations.

## Dependencies & Framework Indicators
- **Frameworks**: Java Swing (standard library GUI toolkit)
- **Manifest**: Managed via Maven `pom.xml`

## Build, Run, and Test Instructions

### Build (Suggested)
```bash
mvn clean compile
```

### Run (Suggested)
```bash
mvn exec:java -Dexec.mainClass="com.copypaste.run.CPMain"
```

### Test (Suggested)
```bash
mvn test
```
