import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@capacitor/core", () => ({
  Capacitor: {
    isNativePlatform: vi.fn(() => false),
    getPlatform: vi.fn(() => "web"),
  },
}));

const getStatus = vi.fn();
const addListener = vi.fn();

vi.mock("@capacitor/network", () => ({
  Network: {
    getStatus,
    addListener,
  },
}));

describe("field-report-network (FR-033)", () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    getStatus.mockResolvedValue({ connected: true });
    addListener.mockResolvedValue({ remove: vi.fn() });

    const { resetCapacitorFieldReportNetworkForTests } = await import(
      "@/lib/capacitor/field-report-network"
    );
    resetCapacitorFieldReportNetworkForTests();
  });

  afterEach(async () => {
    const { resetCapacitorFieldReportNetworkForTests } = await import(
      "@/lib/capacitor/field-report-network"
    );
    resetCapacitorFieldReportNetworkForTests();

    const { Capacitor } = await import("@capacitor/core");
    vi.mocked(Capacitor.isNativePlatform).mockReturnValue(false);
  });

  it("isCapacitorFieldReportNetwork is false on web", async () => {
    const { isCapacitorFieldReportNetwork, refreshCapacitorNetworkStatus } =
      await import("@/lib/capacitor/field-report-network");

    vi.stubGlobal("navigator", { onLine: true });
    expect(isCapacitorFieldReportNetwork()).toBe(false);
    await expect(refreshCapacitorNetworkStatus()).resolves.toBe(true);
    expect(getStatus).not.toHaveBeenCalled();
  });

  it("refreshCapacitorNetworkStatus uses Network.getStatus on native", async () => {
    const { Capacitor } = await import("@capacitor/core");
    vi.mocked(Capacitor.isNativePlatform).mockReturnValue(true);

    getStatus.mockResolvedValue({ connected: false });

    const {
      refreshCapacitorNetworkStatus,
      readCapacitorNetworkConnectedSync,
    } = await import("@/lib/capacitor/field-report-network");

    await expect(refreshCapacitorNetworkStatus()).resolves.toBe(false);
    expect(getStatus).toHaveBeenCalled();
    expect(readCapacitorNetworkConnectedSync()).toBe(false);
  });

  it("subscribeCapacitorNetworkConnectivity notifies on networkStatusChange", async () => {
    const { Capacitor } = await import("@capacitor/core");
    vi.mocked(Capacitor.isNativePlatform).mockReturnValue(true);

    let changeHandler: ((status: { connected: boolean }) => void) | undefined;
    addListener.mockImplementation(async (_event, handler) => {
      changeHandler = handler;
      return { remove: vi.fn() };
    });

    const { subscribeCapacitorNetworkConnectivity } = await import(
      "@/lib/capacitor/field-report-network"
    );

    const listener = vi.fn();
    subscribeCapacitorNetworkConnectivity(listener);

    await vi.waitFor(() => {
      expect(addListener).toHaveBeenCalledWith(
        "networkStatusChange",
        expect.any(Function)
      );
    });

    await vi.waitFor(() => {
      expect(listener).toHaveBeenCalledWith(true);
    });

    listener.mockClear();
    changeHandler?.({ connected: false });

    expect(listener).toHaveBeenCalledWith(false);
  });
});
