import assert from "node:assert/strict";
import test from "node:test";

import {
  CHATGPT_SHORTCUT_NAME,
  gameIdFromAppId,
  launchChatGPT,
  runWithChatGPTForeground,
} from "../src/steam.js";

class MemoryStorage {
  constructor() {
    this.values = new Map();
  }

  getItem(key) {
    return this.values.get(key) ?? null;
  }

  setItem(key, value) {
    this.values.set(key, value);
  }
}

function fixture() {
  const calls = [];
  const apps = {
    async AddShortcut(...args) {
      calls.push(["AddShortcut", ...args]);
      return 0x81234567;
    },
    RunGame(...args) {
      calls.push(["RunGame", ...args]);
    },
    SetShortcutExe(...args) {
      calls.push(["SetShortcutExe", ...args]);
    },
    SetAppLaunchOptions(...args) {
      calls.push(["SetAppLaunchOptions", ...args]);
    },
    SetShortcutIcon(...args) {
      calls.push(["SetShortcutIcon", ...args]);
    },
    SetShortcutName(...args) {
      calls.push(["SetShortcutName", ...args]);
    },
    SetShortcutStartDir(...args) {
      calls.push(["SetShortcutStartDir", ...args]);
    },
  };
  const navigation = {
    MainRunningAppID: 570,
    NavigateToRunningApp() {
      calls.push(["NavigateToRunningApp"]);
    },
    SetRunningApp(appId) {
      calls.push(["SetRunningApp", appId]);
      this.MainRunningAppID = appId;
    },
  };
  const appStore = {
    allApps: [],
    GetAppOverviewByAppID(appId) {
      if (appId !== 570) return undefined;
      return { GetGameID: () => "570" };
    },
  };
  return {
    dependencies: {
      apps,
      appStore,
      navigation,
      storage: new MemoryStorage(),
    },
    calls,
  };
}

test("launchChatGPT creates one Steam shortcut and launches its non-Steam game ID", async () => {
  const { dependencies, calls } = fixture();

  const first = await launchChatGPT(dependencies);
  const second = await launchChatGPT(dependencies);

  assert.equal(first.appId, 0x81234567);
  assert.equal(first.created, true);
  assert.equal(second.created, false);
  assert.equal(
    calls.filter(([name]) => name === "AddShortcut").length,
    1,
  );
  assert.deepEqual(calls.find(([name]) => name === "AddShortcut"), [
    "AddShortcut",
    CHATGPT_SHORTCUT_NAME,
    "/usr/bin/codex-desktop",
    "/opt/codex-desktop",
    'LD_PRELOAD="" %command%',
  ]);
  assert.deepEqual(
    calls.filter(([name]) => name === "SetAppLaunchOptions"),
    [
      [
        "SetAppLaunchOptions",
        0x81234567,
        'LD_PRELOAD="" %command%',
      ],
      [
        "SetAppLaunchOptions",
        0x81234567,
        'LD_PRELOAD="" %command%',
      ],
    ],
  );
  assert.deepEqual(calls.filter(([name]) => name === "RunGame"), [
    ["RunGame", gameIdFromAppId(0x81234567), "", -1, 100],
    ["RunGame", gameIdFromAppId(0x81234567), "", -1, 100],
  ]);
});

test("runWithChatGPTForeground restores the game after the voice command", async () => {
  const { dependencies, calls } = fixture();
  const events = [];

  const result = await runWithChatGPTForeground(dependencies, async () => {
    events.push("voice");
    return { ok: true, message: "Voice Mode toggled" };
  });

  assert.deepEqual(result, { ok: true, message: "Voice Mode toggled" });
  assert.deepEqual(events, ["voice"]);
  const chatLaunch = calls.findIndex(
    (call) => call[0] === "RunGame" && call[1] !== "570",
  );
  const gameRestore = calls.findIndex(
    (call) => call[0] === "RunGame" && call[1] === "570",
  );
  assert.ok(chatLaunch >= 0);
  assert.ok(gameRestore > chatLaunch);
  assert.deepEqual(calls.slice(gameRestore, gameRestore + 3), [
    ["RunGame", "570", "", -1, 100],
    ["SetRunningApp", 570],
    ["NavigateToRunningApp"],
  ]);
});

test("runWithChatGPTForeground restores the game when the command fails", async () => {
  const { dependencies, calls } = fixture();

  await assert.rejects(
    runWithChatGPTForeground(dependencies, async () => {
      throw new Error("voice failed");
    }),
    /voice failed/,
  );

  assert.ok(
    calls.some(
      (call) =>
        call[0] === "RunGame" &&
        call[1] === "570" &&
        call[2] === "" &&
        call[3] === -1 &&
        call[4] === 100,
    ),
  );
});
