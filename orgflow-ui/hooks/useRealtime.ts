"use client";

import {
  useEffect,
} from "react";

import { supabase } from "@/lib/supabase";

type UseRealtimeProps = {

  channelName: string;

  table: string;

  onChange: () => void;
};

export function useRealtime({
  channelName,
  table,
  onChange,
}: UseRealtimeProps) {

  useEffect(() => {

    const channel =
      supabase
      .channel(channelName)
      .on(

        "postgres_changes",

        {

          event: "*",

          schema: "public",

          table,
        },

        () => {

          onChange();
        }
      )
      .subscribe();

    return () => {

      supabase.removeChannel(
        channel
      );
    };

  }, [
    channelName,
    table,
    onChange,
  ]);
}