# cp-master

## Overview

`cp-master` is a Java-based desktop utility application providing a graphical user interface (GUI) for file copy and paste operations. It features asynchronous task execution, memory-mapped file copying, and historical tracking of operations.

## Languages

- **Primary Language:** Java (100% of analyzed source files)

## Directory Layout

- `pom.xml`: Maven project configuration file.
- `src/`
  - `main/`
    - `java/com/copypaste/`: Core package containing application models and interfaces.
      - `adapter/`: Adapters for concurrency (e.g., `CallableAdapter`).
      - `impls/`: Implementation classes for UI, tasks, and memory-mapped copy-paste (`CopyPasteTask`, `CopyPasteUIImpl`, `MemoryMappedCopyPasteImpl`).
      - `logic/`: Business logic interfaces (`CopyPasteLogic`).
      - `run/`: Application startup entry points (`CPMain`).
      - `util/`: Utility and helper classes (`Constants`, `GenericUtil`, `StringSupport`, `Utils`).
    - `resources/script/`: Resource scripts.
  - `test/`
    - `java/com/copypaste/`: Test classes (`CopyPasteTest`).

## Important Modules and Classes

- **`com.copypaste.run.CPMain`**: The main entry point for running the application.
- **`com.copypaste.impls.CopyPasteUIImpl`**: Implements the graphical user interface using Java Swing and `SwingWorker` for background processing and serialization/deserialization of history.
- **`com.copypaste.impls.CopyPasteTask`**: Manages asynchronous file and directory copy operations utilizing `ExecutorService` and futures.
- **`com.copypaste.impls.MemoryMappedCopyPasteImpl`**: Implements memory-mapped file copying logic utilizing `FileChannel` and `ByteBuffer`.
- **`com.copypaste.HistoricalCombo`**: Provides combo-box model support for historical operations.

## Dependencies & Framework Indicators

- **Build System:** Maven (`pom.xml`)
- **Framework Indicators:** Standard Java Swing (`javax.swing`) for UI components and concurrency utilities (`java.util.concurrent`).

## Build, Run, and Test

Refer to the standard Maven build lifecycle commands:

- **Build / Compile:** Managed via `pom.xml`
- **Application Entry Point:** `com.copypaste.run.CPMain`
