import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@capacitor/core", () => ({
  Capacitor: {
    isNativePlatform: vi.fn(() => false),
    getPlatform: vi.fn(() => "web"),
  },
}));

const takePhoto = vi.fn();
const chooseFromGallery = vi.fn();

vi.mock("@capacitor/camera", () => ({
  Camera: {
    takePhoto,
    chooseFromGallery,
  },
  CameraDirection: { Rear: "REAR" },
}));

describe("line-photo-picker (FR-031)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(new Blob(["x"], { type: "image/jpeg" }), {
        status: 200,
      }))
    );
  });

  afterEach(async () => {
    vi.unstubAllGlobals();
    const { Capacitor } = await import("@capacitor/core");
    vi.mocked(Capacitor.isNativePlatform).mockReturnValue(false);
    vi.mocked(Capacitor.getPlatform).mockReturnValue("web");
  });

  it("useNativeLinePhotoCamera is false even on native (WebView file input)", async () => {
    const { Capacitor } = await import("@capacitor/core");
    vi.mocked(Capacitor.isNativePlatform).mockReturnValue(true);
    vi.mocked(Capacitor.getPlatform).mockReturnValue("android");

    const { useNativeLinePhotoCamera, useNativeLinePhotoGallery } =
      await import("@/lib/capacitor/line-photo-picker");

    expect(useNativeLinePhotoCamera()).toBe(false);
    expect(useNativeLinePhotoGallery()).toBe(true);
  });

  it("takeLinePhotoWithNativeCamera is no-op on web", async () => {
    const { takeLinePhotoWithNativeCamera } = await import(
      "@/lib/capacitor/line-photo-picker"
    );

    await expect(takeLinePhotoWithNativeCamera()).resolves.toBeNull();
    expect(takePhoto).not.toHaveBeenCalled();
  });

  it("takeLinePhotoWithNativeCamera returns File on native", async () => {
    const { Capacitor } = await import("@capacitor/core");
    vi.mocked(Capacitor.isNativePlatform).mockReturnValue(true);
    vi.mocked(Capacitor.getPlatform).mockReturnValue("android");

    takePhoto.mockResolvedValue({
      webPath: "capacitor://localhost/cam.jpg",
      metadata: { format: "jpeg" },
    });

    const { takeLinePhotoWithNativeCamera } = await import(
      "@/lib/capacitor/line-photo-picker"
    );

    const file = await takeLinePhotoWithNativeCamera();
    expect(file).toBeInstanceOf(File);
    expect(takePhoto).toHaveBeenCalledWith(
      expect.objectContaining({
        quality: 90,
        cameraDirection: "REAR",
        includeMetadata: true,
      })
    );
  });

  it("returns null when user cancels native camera", async () => {
    const { Capacitor } = await import("@capacitor/core");
    vi.mocked(Capacitor.isNativePlatform).mockReturnValue(true);
    vi.mocked(Capacitor.getPlatform).mockReturnValue("android");

    takePhoto.mockRejectedValue({
      code: "OS-PLUG-CAMR-0006",
      message: "cancelled",
    });

    const { takeLinePhotoWithNativeCamera } = await import(
      "@/lib/capacitor/line-photo-picker"
    );

    await expect(takeLinePhotoWithNativeCamera()).resolves.toBeNull();
  });

  it("pickLinePhotoFromNativeGallery uses chooseFromGallery", async () => {
    const { Capacitor } = await import("@capacitor/core");
    vi.mocked(Capacitor.isNativePlatform).mockReturnValue(true);
    vi.mocked(Capacitor.getPlatform).mockReturnValue("android");

    chooseFromGallery.mockResolvedValue({
      results: [
        {
          webPath: "capacitor://localhost/gallery.jpg",
          metadata: { format: "png" },
        },
      ],
    });

    const { pickLinePhotoFromNativeGallery } = await import(
      "@/lib/capacitor/line-photo-picker"
    );

    const file = await pickLinePhotoFromNativeGallery();
    expect(file?.name).toMatch(/\.png$/);
    expect(chooseFromGallery).toHaveBeenCalledWith(
      expect.objectContaining({
        allowMultipleSelection: false,
        limit: 1,
      })
    );
  });
});
