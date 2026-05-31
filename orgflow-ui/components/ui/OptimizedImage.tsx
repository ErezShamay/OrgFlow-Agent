import Image, { type ImageProps } from "next/image";

export default function OptimizedImage(
  props: ImageProps
) {
  return (
    <Image
      loading={props.loading ?? "lazy"}
      sizes={props.sizes ?? "(max-width: 768px) 100vw, 50vw"}
      quality={props.quality ?? 80}
      {...props}
    />
  );
}
