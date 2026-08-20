import {
  ButtonItem,
  Navigation,
  PanelSection,
  PanelSectionRow,
  staticClasses,
} from "@decky/ui";
import { callable, definePlugin, toaster } from "@decky/api";
import { useEffect, useState } from "react";
import { FaMicrophone } from "react-icons/fa";

type PluginStatus = {
  installed: boolean;
  version: string | null;
  running: boolean;
  voiceCompatible: boolean;
  voiceMessage: string;
  updater: Record<string, unknown> | null;
};

type OperationResult = {
  ok: boolean;
  message: string;
};

const getStatus = callable<[], PluginStatus>("get_status");
const openApp = callable<[], OperationResult>("open_app");
const toggleVoice = callable<[], OperationResult>("toggle_voice");
const newChat = callable<[], OperationResult>("new_chat");
const checkUpdates = callable<[], OperationResult>("check_updates");

const menuCloseDelay = () =>
  new Promise<void>((resolve) => window.setTimeout(resolve, 250));

function Content() {
  const [status, setStatus] = useState<PluginStatus | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = async () => {
    try {
      setStatus(await getStatus());
    } catch (error) {
      console.error("ChatGPT Community status failed", error);
      toaster.toast({
        title: "ChatGPT Community",
        body: "Could not read app status",
      });
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const runOperation = async (
    title: string,
    operation: () => Promise<OperationResult>,
    closeMenus = false,
  ) => {
    setBusy(true);
    try {
      if (closeMenus) {
        Navigation.CloseSideMenus();
        await menuCloseDelay();
      }
      const result = await operation();
      toaster.toast({ title, body: result.message });
      await refresh();
    } catch (error) {
      console.error(`${title} failed`, error);
      toaster.toast({ title, body: "The Decky backend did not respond" });
    } finally {
      setBusy(false);
    }
  };

  const installed = status?.installed === true;
  const compatible = status?.voiceCompatible === true;
  const version = status?.version ?? "not installed";

  return (
    <>
      <PanelSection title="Status">
        <PanelSectionRow>
          <div style={{ width: "100%", lineHeight: 1.5 }}>
            <div>
              <strong>App:</strong>{" "}
              {status === null
                ? "Checking…"
                : status.running
                  ? `Running (${version})`
                  : installed
                    ? `Installed (${version})`
                    : "Not installed"}
            </div>
            <div>
              <strong>Voice Mode:</strong>{" "}
              {status === null
                ? "Checking…"
                : compatible
                  ? "Ready"
                  : "Unavailable"}
            </div>
            {status !== null && !compatible ? (
              <div style={{ opacity: 0.75, marginTop: 4 }}>
                {status.voiceMessage}
              </div>
            ) : null}
          </div>
        </PanelSectionRow>
      </PanelSection>

      <PanelSection title="ChatGPT Community">
        <PanelSectionRow>
          <ButtonItem
            layout="below"
            disabled={busy || !installed}
            onClick={() => void runOperation("Open ChatGPT", openApp, true)}
          >
            Open ChatGPT
          </ButtonItem>
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem
            layout="below"
            disabled={busy || !installed || !compatible}
            onClick={() =>
              void runOperation("ChatGPT Voice Mode", toggleVoice, true)
            }
          >
            Toggle Voice Mode
          </ButtonItem>
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem
            layout="below"
            disabled={busy || !installed}
            onClick={() => void runOperation("New Chat", newChat, true)}
          >
            New Chat
          </ButtonItem>
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem
            layout="below"
            disabled={busy || !installed}
            onClick={() =>
              void runOperation("ChatGPT Updates", checkUpdates)
            }
          >
            Check for Updates
          </ButtonItem>
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem layout="below" disabled={busy} onClick={() => void refresh()}>
            Refresh Status
          </ButtonItem>
        </PanelSectionRow>
      </PanelSection>
    </>
  );
}

export default definePlugin(() => ({
  name: "ChatGPT Community",
  titleView: <div className={staticClasses.Title}>ChatGPT Community</div>,
  content: <Content />,
  icon: <FaMicrophone />,
  alwaysRender: true,
  onDismount() {
    console.log("ChatGPT Community plugin unloaded");
  },
}));
