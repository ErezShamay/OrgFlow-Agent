"use client";

import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import Button from "@/components/ui/Button";
import { apiFetch } from "@/lib/api/client";
import {
  normalizeProjectList,
  readApiErrorMessage,
} from "@/lib/api/read-error-message";
import {
  saveModularTemplateDraft,
  type ModularTemplateDraft,
} from "@/lib/field-reports/modular-template-draft";
import {
  modularBlocksFromTemplateItem,
  TEMPLATE_LIBRARY,
  type TemplateLibraryItem,
} from "@/lib/field-reports/template-library";
import { FR_TOUCH_SELECT } from "@/lib/field-reports/touch-input-class";

type Project = {
  id: string;
  project_name: string;
};

type ProjectPickerDialogProps = {
  open: boolean;
  onClose: () => void;
  initialProjectId?: string;
};

type EntryMode = "project" | "client";

export default function ProjectPickerDialog({
  open,
  onClose,
  initialProjectId = "",
}: ProjectPickerDialogProps) {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [entryMode, setEntryMode] = useState<EntryMode>("project");
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [clientName, setClientName] = useState("");
  const [clientAddress, setClientAddress] = useState("");
  const [selectedTemplate, setSelectedTemplate] =
    useState<TemplateLibraryItem | null>(null);
  const [templatePickerOpen, setTemplatePickerOpen] = useState(false);
  const [expandedCategory, setExpandedCategory] = useState(
    TEMPLATE_LIBRARY[0]?.id ?? ""
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) {
      return;
    }

    let cancelled = false;

    async function loadProjects() {
      setLoading(true);
      setError("");
      setEntryMode("project");
      setSelectedProjectId("");
      setClientName("");
      setClientAddress("");
      setSelectedTemplate(null);
      setTemplatePickerOpen(false);

      try {
        const response = await apiFetch("/projects");
        if (!response.ok) {
          throw new Error(
            await readApiErrorMessage(
              response,
              "טעינת רשימת הפרויקטים נכשלה"
            )
          );
        }

        const payload = await response.json();
        const projectList = normalizeProjectList(payload) as Project[];

        if (cancelled) {
          return;
        }

        setProjects(projectList);
        if (initialProjectId && projectList.some((p) => p.id === initialProjectId)) {
          setEntryMode("project");
          setSelectedProjectId(initialProjectId);
        } else if (projectList.length === 1) {
          setSelectedProjectId(projectList[0].id);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "טעינת רשימת הפרויקטים נכשלה"
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadProjects();

    return () => {
      cancelled = true;
    };
  }, [open, initialProjectId]);

  useEffect(() => {
    if (!open) {
      return;
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        if (templatePickerOpen) {
          setTemplatePickerOpen(false);
          return;
        }
        onClose();
      }
    }

    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("keydown", handleEscape);
    };
  }, [open, onClose, templatePickerOpen]);

  if (!open) {
    return null;
  }

  const sourceValid =
    entryMode === "project"
      ? Boolean(selectedProjectId)
      : Boolean(clientName.trim() && clientAddress.trim());

  const canContinue = Boolean(sourceValid && selectedTemplate);

  function buildModularDraft(): ModularTemplateDraft | null {
    if (!selectedTemplate) {
      return null;
    }

    return {
      templateId: selectedTemplate.id,
      templateLabel: selectedTemplate.label_he,
      visitType: selectedTemplate.visitType,
      name: selectedTemplate.label_he,
      examplePdf: selectedTemplate.examplePdf,
      includeFixedTextBlocks: true,
      blocks: modularBlocksFromTemplateItem(selectedTemplate),
    };
  }

  function handleContinue() {
    if (!canContinue || !selectedTemplate) {
      return;
    }

    const draft = buildModularDraft();
    const query = new URLSearchParams({
      template: selectedTemplate.id,
      source: entryMode,
      visit_type: selectedTemplate.visitType,
    });

    if (draft) {
      const key = saveModularTemplateDraft(draft);
      if (key) {
        query.set("modular_template_key", key);
      }
    }

    if (entryMode === "project") {
      query.set("project", selectedProjectId);
    } else {
      query.set("client_name", clientName.trim());
      query.set("client_address", clientAddress.trim());
    }

    onClose();
    router.push(`/field-reports/new?${query.toString()}`);
  }

  function handleSelectTemplate(item: TemplateLibraryItem) {
    setSelectedTemplate(item);
    setTemplatePickerOpen(false);
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-4 sm:items-center"
      role="presentation"
      onClick={onClose}
    >
      <div
        className="max-h-[90vh] w-full max-w-lg space-y-4 overflow-y-auto rounded-2xl border border-zinc-200 bg-white p-6 shadow-xl dark:border-zinc-700 dark:bg-zinc-900"
        role="dialog"
        aria-modal="true"
        aria-labelledby="project-picker-title"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 id="project-picker-title" className="text-lg font-semibold">
          יצירת דוח
        </h2>

        <p className="text-sm text-zinc-600 dark:text-zinc-300">
          בחר מקור לדוח, ואז בחר תבנית לעבודה.
        </p>

        {loading ? (
          <div className="flex items-center gap-2 text-sm text-zinc-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            טוען נתונים...
          </div>
        ) : error ? (
          <p className="text-sm text-red-600">{error}</p>
        ) : (
          <div className="space-y-4">
            <fieldset className="space-y-2">
              <legend className="text-sm font-medium">מקור הדוח</legend>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  name="entry-mode"
                  value="project"
                  checked={entryMode === "project"}
                  onChange={() => setEntryMode("project")}
                />
                עם פרויקט
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  name="entry-mode"
                  value="client"
                  checked={entryMode === "client"}
                  onChange={() => setEntryMode("client")}
                />
                ללא פרויקט (שם לקוח)
              </label>
            </fieldset>

            {entryMode === "project" ? (
              <div>
                <label
                  htmlFor="report-project-picker"
                  className="mb-2 block text-sm font-medium"
                >
                  פרויקט
                </label>
                <select
                  id="report-project-picker"
                  value={selectedProjectId}
                  onChange={(event) => setSelectedProjectId(event.target.value)}
                  className={FR_TOUCH_SELECT}
                >
                  <option value="">בחר פרויקט</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.project_name}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div className="space-y-3">
                <label className="block space-y-1 text-sm">
                  <span className="font-medium">שם לקוח</span>
                  <input
                    className="of-input w-full"
                    value={clientName}
                    onChange={(event) => setClientName(event.target.value)}
                    placeholder="הזן שם לקוח"
                  />
                </label>
                <label className="block space-y-1 text-sm">
                  <span className="font-medium">כתובת</span>
                  <input
                    className="of-input w-full"
                    value={clientAddress}
                    onChange={(event) => setClientAddress(event.target.value)}
                    placeholder="הזן כתובת"
                  />
                </label>
              </div>
            )}

            <section className="space-y-2 rounded-xl border border-zinc-200 p-3 dark:border-zinc-700">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-sm font-medium">תבנית</p>
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setTemplatePickerOpen(true)}
                >
                  בחירת תבנית
                </Button>
              </div>
              {selectedTemplate ? (
                <p className="text-sm text-zinc-600 dark:text-zinc-300">
                  נבחרה: {selectedTemplate.label_he}
                  {selectedTemplate.examplePdf ? (
                    <span className="mt-1 block text-xs text-zinc-500">
                      דוגמה: {selectedTemplate.examplePdf}
                    </span>
                  ) : null}
                </p>
              ) : (
                <p className="text-sm text-amber-700 dark:text-amber-300">
                  יש לבחור תבנית לפני המשך.
                </p>
              )}
            </section>

            {selectedTemplate ? (
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-700 dark:bg-zinc-800/40">
                  <p className="mb-2 text-xs font-semibold text-zinc-500">
                    מבנה התבנית
                  </p>
                  <ul className="space-y-1">
                    {selectedTemplate.blocks.map((block) => (
                      <li
                        key={`${selectedTemplate.id}-${block.title_he}`}
                        className="rounded bg-white px-2 py-1 text-xs dark:bg-zinc-900"
                      >
                        {block.title_he}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="rounded-lg border border-zinc-200 bg-white p-3 dark:border-zinc-700 dark:bg-zinc-900">
                  <p className="mb-2 text-xs font-semibold text-zinc-500">
                    תצוגה מקדימה
                  </p>
                  <div className="space-y-2">
                    {selectedTemplate.blocks.map((block) => (
                      <div
                        key={`preview-${block.title_he}`}
                        className="rounded border border-zinc-200 p-2 dark:border-zinc-700"
                      >
                        <p className="text-xs font-semibold">{block.title_he}</p>
                        {block.kind === "findings_table"
                          || block.kind === "progress_table" ? (
                          <div className="mt-1 space-y-1">
                            <div className="h-1.5 rounded bg-zinc-100 dark:bg-zinc-800" />
                            <div className="h-1.5 rounded bg-zinc-100 dark:bg-zinc-800" />
                          </div>
                        ) : (
                          <p className="text-[10px] text-zinc-500">...</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        )}

        <div className="flex flex-wrap justify-end gap-2">
          <Button variant="secondary" type="button" onClick={onClose}>
            ביטול
          </Button>
          <Button
            type="button"
            disabled={!canContinue || loading}
            onClick={handleContinue}
          >
            יצירת דוח
          </Button>
        </div>
      </div>

      {templatePickerOpen ? (
        <div
          className="fixed inset-0 z-[60] flex items-end justify-center bg-black/40 p-4 sm:items-center"
          role="presentation"
          onClick={() => setTemplatePickerOpen(false)}
        >
          <div
            className="max-h-[80vh] w-full max-w-lg space-y-3 overflow-y-auto rounded-2xl border border-zinc-200 bg-white p-5 shadow-xl dark:border-zinc-700 dark:bg-zinc-900"
            role="dialog"
            aria-modal="true"
            aria-labelledby="template-picker-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-center justify-between gap-2">
              <h3 id="template-picker-title" className="text-lg font-semibold">
                בחירת תבנית
              </h3>
              <button
                type="button"
                className="rounded-md px-2 py-1 text-sm text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                onClick={() => setTemplatePickerOpen(false)}
              >
                ✕
              </button>
            </div>

            <p className="text-sm text-zinc-600 dark:text-zinc-300">
              בחר תבנית לדוגמה לפי קטגוריה. המבנה נבנה לפי מבנה הדוח.
            </p>

            {TEMPLATE_LIBRARY.map((category) => {
              const isOpen = expandedCategory === category.id;
              return (
                <section
                  key={category.id}
                  className="rounded-xl border border-zinc-200 dark:border-zinc-700"
                >
                  <button
                    type="button"
                    className="flex w-full items-center justify-between px-4 py-3 text-right text-sm font-medium hover:bg-zinc-50 dark:hover:bg-zinc-800/60"
                    onClick={() =>
                      setExpandedCategory(isOpen ? "" : category.id)
                    }
                  >
                    <span>{category.title_he}</span>
                    <span>{isOpen ? "▴" : "▾"}</span>
                  </button>
                  {isOpen ? (
                    <ul className="border-t border-zinc-200 dark:border-zinc-700">
                      {category.items.map((item) => (
                        <li key={item.id}>
                          <button
                            type="button"
                            className="flex w-full items-center justify-between px-4 py-2 text-right text-sm hover:bg-zinc-50 dark:hover:bg-zinc-800/60"
                            onClick={() => handleSelectTemplate(item)}
                          >
                            <span>{item.label_he}</span>
                            <span className="text-zinc-400">‹</span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </section>
              );
            })}
          </div>
        </div>
      ) : null}
    </div>
  );
}
