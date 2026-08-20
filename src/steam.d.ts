export const CHATGPT_SHORTCUT_NAME: string;

export type SteamApps = {
  AddShortcut(
    name: string,
    executable: string,
    startDirectory: string,
    launchOptions: string,
  ): Promise<number>;
  RunGame(
    gameId: string,
    launchOptions: string,
    launchOption: number,
    launchSource: number,
  ): void;
  SetShortcutExe(appId: number, executable: string): void;
  SetShortcutName(appId: number, name: string): void;
  SetShortcutStartDir(appId: number, directory: string): void;
};

export type SteamNavigation = {
  MainRunningAppID: number;
  NavigateToRunningApp(): void;
  SetRunningApp(appId: number): void;
};

export type SteamAppStore = {
  allApps: Array<{ appid: number; display_name: string }>;
  GetAppOverviewByAppID(
    appId: number,
  ): { GetGameID(): string } | undefined;
};

export type SteamDependencies = {
  apps: SteamApps;
  appStore: SteamAppStore;
  navigation: SteamNavigation;
  storage: Storage;
};

export function gameIdFromAppId(appId: number): string;

export function launchChatGPT(
  dependencies: SteamDependencies,
): Promise<{ appId: number; created: boolean }>;

export function runWithChatGPTForeground<T>(
  dependencies: SteamDependencies,
  operation: () => Promise<T>,
): Promise<T>;
