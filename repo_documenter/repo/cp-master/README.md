# cp-master

## Overview
cp-master is a Java-based desktop application designed around file copying and paste operations, featuring a graphical user interface (GUI) built with Java Swing and multi-threaded task management.

## Languages
- **Primary Language**: Java (15 files)

## Directory Layout & Important Modules
The project structure is organized under `src/main/java/com/copypaste` with the following key packages and classes:

- **`com.copypaste`**
  - `CopyPasteUI.java`: Interface definition for the copy/paste user interface.
  - `CopyPasteUI`: Core UI structure with `build` and `showUI` methods.
  - `HistoricalCombo.java`: JComboBox component managing history and action listeners.
  - `HistoricalJList.java`: JList component for historical data.
  - `Task.java`: Interface defining task control lifecycle methods (`start`, `stop`, `terminate`, `finish`, `size`, `completedSize`, `getSummary`).
  - `CopyPasteTest.java`: Test class located under `src/test/java/com/copypaste`.
- **`com.copypaste.adapter`**
  - `CallableAdapter.java`: Adapts copy/paste logic to `Callable` tasks.
- **`com.copypaste.impls`**
  - `CopyPasteTask.java`: Implementation of file and directory copy/paste execution using `ExecutorService` and background workers.
  - `CopyPasteUIImpl.java`: Swing-based implementation of the UI (`CopyPasteUIImpl`, `SwingWorker` task execution, component initialization, and serialization support).
  - `MemoryMappedCopyPasteImpl.java`: File copy implementation utilizing `RandomAccessFile`, `ByteBuffer`, and `FileChannel` (memory-mapped files).
- **`com.copypaste.logic`**
  - `CopyPasteLogic.java`: Core logic interface for copy/paste operations (`copyPaste`, `isCopied`, `size`).
- **`com.copypaste.run`**
  - `CPMain.java`: Application entry point.
- **`com.copypaste.util`**
  - `Constants.java`: Shared options and state definitions.
  - `GenericUtil.java`: Utility methods (e.g., `toList`).
  - `StringSupport.java`: String validation helpers (e.g., `isEmpty`).
  - `Utils.java`: Helper utilities for window management, messaging, and memory copy/paste instance retrieval.

## Entry Points
- **Application Main Class**: `com.copypaste.run.CPMain` (invokes `CopyPasteUIImpl.main`) located in `src/main/java/com/copypaste/run/CPMain.java`.

## Dependencies & Build Configuration
- **Build System**: Maven (`pom.xml`)
- **Dependencies**: Not identified from static analysis.
- **Framework Indicators**: Java Swing

## Build, Run, and Test
- Build and test commands can be executed using Maven via `pom.xml`, though explicit CLI build commands are not identified from static analysis.
