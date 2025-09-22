/**
 * Edit Crawl Configuration Dialog
 * Allows editing existing crawler configuration for knowledge items
 */

import { AlertCircle, Globe, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useToast } from "../../ui/hooks/useToast";
import { Button, Input, Label } from "../../ui/primitives";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "../../ui/primitives/dialog";
import { useKnowledgeItem, useUpdateCrawlConfig } from "../hooks";
import type { CrawlConfig } from "../types";
import { AdvancedCrawlConfig } from "./AdvancedCrawlConfig";
import { KnowledgeTypeSelector } from "./KnowledgeTypeSelector";
import { LevelSelector } from "./LevelSelector";
import { TagInput } from "./TagInput";

interface EditCrawlConfigDialogProps {
  sourceId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export const EditCrawlConfigDialog: React.FC<EditCrawlConfigDialogProps> = ({
  sourceId,
  open,
  onOpenChange,
  onSuccess,
}) => {
  const { showToast } = useToast();
  const { data: item, isLoading: itemLoading } = useKnowledgeItem(sourceId);
  const updateMutation = useUpdateCrawlConfig();

  // Form state
  const [url, setUrl] = useState("");
  const [knowledgeType, setKnowledgeType] = useState<"technical" | "business">("technical");
  const [maxDepth, setMaxDepth] = useState("2");
  const [tags, setTags] = useState<string[]>([]);
  const [crawlConfig, setCrawlConfig] = useState<CrawlConfig>({});

  // Load existing configuration when item loads
  useEffect(() => {
    if (item) {
      setUrl(item.url || "");
      setKnowledgeType(item.knowledge_type || "technical");
      // Access max_depth from metadata as any since it's not typed
      const metadata = item.metadata as any;
      setMaxDepth(metadata?.max_depth?.toString() || "2");
      setTags(metadata?.tags || []);

      // Load existing crawl config if available
      if (metadata?.crawl_config) {
        setCrawlConfig(metadata.crawl_config);
      }
    }
  }, [item]);

  const handleSave = async () => {
    if (!url) {
      showToast("URL is required", "error");
      return;
    }

    try {
      await updateMutation.mutateAsync({
        sourceId,
        url,
        knowledge_type: knowledgeType,
        max_depth: parseInt(maxDepth, 10),
        tags: tags.length > 0 ? tags : undefined,
        crawl_config: crawlConfig,
      });

      showToast("Configuration updated. Recrawl initiated.", "success");
      onSuccess?.();
      onOpenChange(false);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to update configuration";
      showToast(message, "error");
    }
  };

  const isProcessing = updateMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[85vh] overflow-hidden flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle>Edit Crawler Configuration</DialogTitle>
          <DialogDescription>
            Update the crawler settings for this knowledge item
          </DialogDescription>
        </DialogHeader>

        {itemLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-cyan-400" />
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto pr-2">
            <div className="space-y-6 pb-4">
              {/* Warning Alert */}
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4 flex gap-3">
                <AlertCircle className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-amber-200">
                  Saving changes will trigger a recrawl with the new configuration.
                  Existing documents will be replaced with newly crawled content.
                </div>
              </div>

              {/* URL Input */}
              <div className="space-y-2">
                <Label className="text-sm font-medium text-gray-900 dark:text-white/90">
                  Website URL
                </Label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Globe className="h-5 w-5" style={{ color: "#0891b2" }} />
                  </div>
                  <Input
                    type="url"
                    placeholder="https://docs.example.com"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    disabled={isProcessing}
                    className="pl-10 h-12 backdrop-blur-md bg-gradient-to-r from-white/60 to-white/50 dark:from-black/60 dark:to-black/50"
                  />
                </div>
              </div>

              {/* Advanced Configuration */}
              <AdvancedCrawlConfig config={crawlConfig} onChange={setCrawlConfig} />

              {/* Knowledge Type */}
              <KnowledgeTypeSelector
                value={knowledgeType}
                onValueChange={setKnowledgeType}
                disabled={isProcessing}
              />

              {/* Crawl Depth */}
              <LevelSelector
                value={maxDepth}
                onValueChange={setMaxDepth}
                disabled={isProcessing}
              />

              {/* Tags */}
              <TagInput
                tags={tags}
                onTagsChange={setTags}
                disabled={isProcessing}
                placeholder="Add tags like 'api', 'documentation', 'guide'..."
              />

              {/* Action Buttons */}
              <div className="flex gap-2 pt-4">
                <Button
                  variant="ghost"
                  onClick={() => onOpenChange(false)}
                  disabled={isProcessing}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={isProcessing || !url}
                  className="flex-1 bg-gradient-to-r from-cyan-500 to-cyan-600 hover:from-cyan-600 hover:to-cyan-700"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Updating & Recrawling...
                    </>
                  ) : (
                    <>
                      <Globe className="w-4 h-4 mr-2" />
                      Save & Recrawl
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};