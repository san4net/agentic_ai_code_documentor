# cp-master

## Overview

`cp-master` is a Java-based desktop application providing file copy and paste capabilities with a graphical user interface (GUI). It leverages Swing components, concurrent task execution, and memory-mapped file operations.

## Languages

- **Primary Language:** Java (100% of analyzed source files)

## Directory Layout & Important Modules

The project structure is organized under `src/main/java/com/copypaste/`:

- **`com.copypaste`**: Core interfaces and UI contracts (`CopyPasteUI.java`, `Task.java`, `HistoricalCombo.java`, `HistoricalJList.java`, `CopyPasteTest.java`)
- **`com.copypaste.adapter`**: Adapters bridging logic and concurrency (`CallableAdapter.java`)
- **`com.copypaste.impls`**: Implementations for UI, copy-paste tasks, and memory mapping (`CopyPasteTask.java`, `CopyPasteUIImpl.java`, `MemoryMappedCopyPasteImpl.java`)
- **`com.copypaste.logic`**: Core copy-paste business logic definitions (`CopyPasteLogic.java`)
- **`com.copypaste.run`**: Application entry point (`CPMain.java`)
- **`com.copypaste.util`**: Utility and helper classes (`Constants.java`, `GenericUtil.java`, `StringSupport.java`, `Utils.java`)
- **`src/main/resources/script/`**: Contains resource scripts (Not identified from static analysis)

## Classes and Functions

### Core Interfaces & Logic
- **`Task`**: Defines lifecycle and status methods (`start`, `stop`, `terminate`, `finish`, `size`, `completedSize`, `getSummary`).
- **`CopyPasteLogic`**: Defines core logic methods (`copyPaste`, `isCopied`, `size`).

### Implementations
- **`CopyPasteTask`**: Manages asynchronous file/directory copy operations using `ExecutorService`, `Future`, and worker threads.
- **`CopyPasteUIImpl`**: Implements the Swing GUI (`CopyPasteUI`), handling user actions, component building, event listeners, property changes, and state serialization/deserialization.
- **`MemoryMappedCopyPasteImpl`**: Implements memory-mapped file copying using `RandomAccessFile` and `FileChannel`.
- **`CallableAdapter`**: Adapts `CopyPasteLogic` to the `Callable` interface.

### UI & Utilities
- **`CopyPasteUI`**: Abstract interface/class for user interface definition.
- **`HistoricalCombo`**: JComboBox extension with action listeners for managing history.
- **`Utils`**: Provides window adapter configurations, null-checks, message dialogs, and memory-mapped copy-paste utility retrieval.
- **`Constants`**: Holds application constants including copy options and states.
- **`GenericUtil` & `StringSupport`**: General utility helpers (e.g., `toList`, `isEmpty`).

## Dependencies & Build System

- **Build Tool:** Maven (`pom.xml`)
- **External Dependencies:** Not identified from static analysis
- **Framework Indicators:** Java Swing (GUI components)

## Entry Points & Execution

- **Main Entry Point:** `com.copypaste.run.CPMain` (`main` method invokes `CopyPasteUIImpl`).
- **Build / Run / Test Commands:** Rely on standard Maven commands (e.g., `mvn clean compile`, `mvn test`) as defined by the presence of `pom.xml`.
