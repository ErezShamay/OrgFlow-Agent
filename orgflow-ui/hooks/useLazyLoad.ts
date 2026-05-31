"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import { observeLazyElement } from "@/lib/ui/lazy";

export function useLazyLoad(onVisible: () => void) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const element = ref.current;

    if (!element || isVisible) {
      return;
    }

    return observeLazyElement(element, () => {
      setIsVisible(true);
      onVisible();
    });
  }, [isVisible, onVisible]);

  return {
    ref,
    isVisible,
  };
}
