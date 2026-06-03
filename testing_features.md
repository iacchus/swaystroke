# How to Test the Advanced Features

This document provides instructions on how to test the 5 new advanced features once they are implemented on the `dev` branch.

## 1. GUI Management
1. Run `swaystroke list-gui`.
2. Click the **Delete** button next to a gesture and verify it disappears.
3. Click the **Re-record** button next to a gesture. The GTK overlay should appear. Draw a new shape, and verify the gesture is updated but retains its old command.

## 2. Daemon Mode & Zero Latency
1. Run `swaystroke daemon &` to start the background process. It will run silently.
2. Run `swaystroke trigger`.
3. The transparent overlay should appear **instantly** without the normal Python startup delay. Draw your gesture.
4. The overlay should hide itself and execute the command, remaining running in the background for the next trigger.
5. Kill the daemon when finished: `pkill -f "swaystroke daemon"`.

## 3. Native Key Presses / Text Input
1. Record a native keystroke: `swaystroke record --type key "Copy" "ctrl+c"`
2. Record native text: `swaystroke record --type text "Greeting" "Hello World!"`
3. Trigger the gesture using `swaystroke listen` or `swaystroke trigger`.
4. Verify that `swaystroke` directly emits the keystrokes or types the text using `wtype` (or `ydotool`), rather than you needing to write a bash wrapper.

## 4. Advanced Recognition (Multi-stroke & Direction Invariance)
1. **Multi-stroke:** Run `swaystroke record "cross" "echo X"`. Draw a diagonal line, release the mouse, then quickly draw the intersecting line. Wait for the timeout (e.g., 500ms) to finalize the gesture.
2. **Direction Invariance:** Record a circle drawn clockwise. Then run `swaystroke listen` and draw the same circle **counter-clockwise**. It should still recognize it with a high score.

## 5. Advanced Triggers & Visual Configurations
1. Open `~/.config/swaystroke/config.py` (or the local `config.py` if testing locally) and modify `LINE_COLOR` or `LINE_WIDTH`.
2. Run `swaystroke listen` and verify the drawing trail reflects the new visual configuration.
3. Test the idle timeout for multi-strokes (configurable via `MULTISTROKE_TIMEOUT`). If you hold the mouse still, or wait longer than the timeout after lifting the mouse, it should finalize or cancel the stroke accordingly.
