# cp-master

## Overview

`cp-master` is a Java-based desktop application providing file copy and paste utilities with a Swing user interface. The project includes asynchronous task execution, memory-mapped file operations, historical action tracking, and serialization support.

## Languages

- **Primary Language:** Java (15 source/test files)

## Directory Layout

The repository structure is organized as follows:

- `pom.xml`: Maven build configuration and project manifest.
- `src/main/java/com/copypaste/`: Core package containing main application interfaces, tasks, and historical UI components.
  - `adapter/`: Adapters for concurrent execution (e.g., `CallableAdapter`).
  - `impls/`: Implementations of core logic, user interfaces, tasks, and memory-mapped operations.
  - `logic/`: Business logic interfaces (`CopyPasteLogic`).
  - `run/`: Entry point classes (`CPMain`).
  - `util/`: Utility classes (`Constants`, `GenericUtil`, `StringSupport`, `Utils`).
- `src/main/resources/`: Application resources and scripts.
- `src/test/java/com/copypaste/`: Test classes (`CopyPasteTest`).

## Important Modules & Classes

- **UI Components:**
  - `CopyPasteUI` / `CopyPasteUIImpl`: Swing-based user interface, builders, and background workers (`SwingWorker`) handling user interactions, serialization, and progress reporting.
  - `HistoricalCombo` / `HistoricalJList`: Components supporting historical record presentation and user actions.
- **Copy & Paste Logic:**
  - `CopyPasteTask`: Manages asynchronous copy/paste operations using an `ExecutorService` and tracks progress/state.
  - `MemoryMappedCopyPasteImpl`: Implements file copying using memory-mapped buffers (`FileChannel` and `ByteBuffer`).
  - `CopyPasteLogic`: Interface defining core copy/paste operations.
- **Utilities & Helpers:**
  - `Constants`: Defines system states and copy options.
  - `Utils`: Provides window listeners, message dialogs, and helper initializers.

## Entry Points

- `com.copypaste.run.CPMain`: Main entry point launching `CopyPasteUIImpl`.

## Build, Run, and Test

Build and execution rely on standard Maven commands as defined by `pom.xml`:

- **Build / Compile:** Managed via Maven (`pom.xml`).
- **Test:** Run tests located in `src/test/java/com/copypaste/CopyPasteTest.java` using Maven test phases.
- **Run:** Execute the `main` method in `com.copypaste.run.CPMain` to start the Swing graphical user interface.

## Dependencies

- Not identified from static analysis (Managed via `pom.xml`).
