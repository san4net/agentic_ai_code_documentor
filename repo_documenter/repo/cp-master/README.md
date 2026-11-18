# cp-master

## Overview
cp-master is a Java application featuring a Swing-based user interface for managing file copy and paste tasks. It supports advanced features such as memory-mapped file operations, historical selection tracking, and asynchronous task execution.

## Languages
- **Primary Language:** Java (15 files)

## Directory Layout
- `pom.xml`
- `src/`
  - `main/`
    - `java/com/copypaste/`
      - `adapter/`: Adapters for task execution (`CallableAdapter.java`)
      - `impls/`: Implementation classes for UI, background tasks, and memory-mapped copying (`CopyPasteTask.java`, `CopyPasteUIImpl.java`, `MemoryMappedCopyPasteImpl.java`)
      - `logic/`: Business logic interfaces (`CopyPasteLogic.java`)
      - `run/`: Application entry point (`CPMain.java`)
      - `util/`: Utility and constant helper classes (`Constants.java`, `GenericUtil.java`, `StringSupport.java`, `Utils.java`)
      - `CopyPasteUI.java`, `HistoricalCombo.java`, `HistoricalJList.java`, `Task.java`
    - `resources/script/`
  - `test/`
    - `java/com/copypaste/`: Test classes (`CopyPasteTest.java`)

## Important Modules & Classes
- **`com.copypaste.run.CPMain`**: Entry point for launching the application.
- **`com.copypaste.impls.CopyPasteUIImpl`**: Manages the Swing user interface, background workers, event handling, component initialization, and state serialization/deserialization.
- **`com.copypaste.impls.CopyPasteTask`**: Handles asynchronous copy-paste execution and task tracking.
- **`com.copypaste.impls.MemoryMappedCopyPasteImpl`**: Implements memory-mapped file copy and paste logic using Java NIO channels and byte buffers.
- **`com.copypaste.HistoricalCombo`**: Provides combo box models and action handling for historical entries.

## Dependencies and Framework Indicators
- Project build and dependency management configured via Maven (`pom.xml`).
- Uses standard Java Swing libraries for the graphical user interface and `java.util.concurrent` for concurrency.

## Entry Points
- **Main Class**: `com.copypaste.run.CPMain`

## Build and Run Suggestions
- **Build**: `mvn clean package`
- **Run**: `mvn exec:java -Dexec.mainClass="com.copypaste.run.CPMain"`
- **Test**: `mvn test`
