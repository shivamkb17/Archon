import { useState, useMemo } from "react";
import {
  Link as LinkIcon,
  Upload,
  Trash2,
  RefreshCw,
  Code,
  FileText,
  Brain,
  Box as BoxIcon,
  Globe,
  ChevronRight,
  Pencil,
} from "lucide-react";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import {
  KnowledgeItem,
  KnowledgeItemMetadata,
} from "../../services/knowledgeBaseService";
import { useCardTilt } from "../../hooks/useCardTilt";
import { CodeViewerModal, CodeExample } from "../code/CodeViewerModal";
import { EditKnowledgeItemModal } from "./EditKnowledgeItemModal";
import "../../styles/card-animations.css";

// Define GroupedKnowledgeItem interface locally
interface GroupedKnowledgeItem {
  id: string;
  title: string;
  domain: string;
  items: KnowledgeItem[];
  metadata: KnowledgeItemMetadata;
  created_at: string;
  updated_at: string;
}

// Helper function to guess language from title
const guessLanguageFromTitle = (title: string = ""): string => {
  const titleLower = title.toLowerCase();
  if (titleLower.includes("javascript") || titleLower.includes("js"))
    return "javascript";
  if (titleLower.includes("typescript") || titleLower.includes("ts"))
    return "typescript";
  if (titleLower.includes("react")) return "jsx";
  if (titleLower.includes("html")) return "html";
  if (titleLower.includes("css")) return "css";
  if (titleLower.includes("python")) return "python";
  if (titleLower.includes("java")) return "java";
  return "javascript"; // Default
};

// Tags display component
interface TagsDisplayProps {
  tags: string[];
}

const TagsDisplay = ({ tags }: TagsDisplayProps) => {
  const [showTooltip, setShowTooltip] = useState(false);

  if (!tags || tags.length === 0) return null;

  const visibleTags = tags.slice(0, 4);
  const remainingTags = tags.slice(4);
  const hasMoreTags = remainingTags.length > 0;

  return (
    <div className="w-full">
      <div className="flex flex-wrap gap-2 h-full">
        {visibleTags.map((tag, index) => (
          <Badge
            key={index}
            color="purple"
            variant="outline"
            className="text-xs"
          >
            {tag}
          </Badge>
        ))}
        {hasMoreTags && (
          <div
            className="cursor-pointer relative"
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
          >
            <Badge
              color="purple"
              variant="outline"
              className="bg-purple-100/50 dark:bg-purple-900/30 border-dashed text-xs"
            >
              +{remainingTags.length} more...
            </Badge>
            {showTooltip && (
              <div className="absolute top-full mt-2 left-1/2 transform -translate-x-1/2 bg-black dark:bg-zinc-800 text-white text-xs rounded-lg py-2 px-3 shadow-lg z-50 whitespace-nowrap max-w-xs">
                <div className="font-semibold text-purple-300 mb-1">
                  Additional Tags:
                </div>
                {remainingTags.map((tag, index) => (
                  <div key={index} className="text-gray-300">
                    • {tag}
                  </div>
                ))}
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-b-black dark:border-b-zinc-800"></div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Delete confirmation modal component
interface DeleteConfirmModalProps {
  onConfirm: () => void;
  onCancel: () => void;
  title: string;
  message: string;
}

const DeleteConfirmModal = ({
  onConfirm,
  onCancel,
  title,
  message,
}: DeleteConfirmModalProps) => {
  return (
    <div className="fixed inset-0 bg-gray-500/50 dark:bg-black/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="w-full max-w-md">
        <Card className="w-full">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
            {title}
          </h3>
          <p className="text-gray-600 dark:text-zinc-400 mb-6">{message}</p>
          <div className="flex justify-end gap-4">
            <button
              onClick={onCancel}
              className="px-4 py-2 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={onConfirm}
              className="px-4 py-2 bg-pink-500 text-white rounded-md hover:bg-pink-600 transition-colors"
            >
              Delete
            </button>
          </div>
        </Card>
      </div>
    </div>
  );
};

interface GroupedKnowledgeItemCardProps {
  groupedItem: GroupedKnowledgeItem;
  onDelete: (sourceId: string) => void;
  onUpdate?: () => void;
  onRefresh?: (sourceId: string) => void;
}

export const GroupedKnowledgeItemCard = ({
  groupedItem,
  onDelete,
  onUpdate,
  onRefresh,
}: GroupedKnowledgeItemCardProps) => {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  const [showCodeTooltip, setShowCodeTooltip] = useState(false);
  const [showPageTooltip, setShowPageTooltip] = useState(false);
  const [isRemoving, setIsRemoving] = useState(false);
  const [activeCardIndex, setActiveCardIndex] = useState(0);
  const [isShuffling, setIsShuffling] = useState(false);
  const [showCodeModal, setShowCodeModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);

  const isGrouped = groupedItem.items.length > 1;
  const activeItem = groupedItem.items[activeCardIndex];

  // Updated color logic based on individual item's source type and knowledge type
  const getCardColor = (item: KnowledgeItem) => {
    if (item.metadata.source_type === "url") {
      // Web documents
      return item.metadata.knowledge_type === "technical" ? "blue" : "cyan";
    } else {
      // Uploaded documents
      return item.metadata.knowledge_type === "technical" ? "purple" : "pink";
    }
  };

  // Use active item for main card color
  const accentColor = getCardColor(activeItem);

  // Updated icon colors to match active card
  const getSourceIconColor = (item: KnowledgeItem) => {
    if (item.metadata.source_type === "url") {
      return item.metadata.knowledge_type === "technical"
        ? "text-blue-500"
        : "text-cyan-500";
    } else {
      return item.metadata.knowledge_type === "technical"
        ? "text-purple-500"
        : "text-pink-500";
    }
  };

  const getTypeIconColor = (item: KnowledgeItem) => {
    if (item.metadata.source_type === "url") {
      return item.metadata.knowledge_type === "technical"
        ? "text-blue-500"
        : "text-cyan-500";
    } else {
      return item.metadata.knowledge_type === "technical"
        ? "text-purple-500"
        : "text-pink-500";
    }
  };

  // Use active item for icons
  // const TypeIcon = activeItem.metadata.knowledge_type === 'technical' ? BoxIcon : Brain;
  // const sourceIconColor = getSourceIconColor(activeItem);
  // const typeIconColor = getTypeIconColor(activeItem);

  const statusColorMap = {
    active: "green",
    processing: "blue",
    error: "pink",
  };

  // Use the tilt effect hook - but only apply the handlers if not grouped
  const { cardRef, tiltStyles, handlers } = useCardTilt({
    max: 10,
    scale: 1.02,
    perspective: 1200,
  });

  // Only use tilt handlers if not grouped and modal is not open
  const tiltHandlers = isGrouped || showCodeModal ? {} : handlers;

  const handleDelete = () => {
    setIsRemoving(true);
    // Delay the actual deletion to allow for the animation
    setTimeout(() => {
      onDelete(groupedItem.id);
      setShowDeleteConfirm(false);
    }, 500);
  };

  const handleRefresh = () => {
    if (onRefresh && activeItem) {
      onRefresh(activeItem.source_id);
    }
  };

  // Calculate total word count
  // const totalWordCount = groupedItem.metadata.word_count || groupedItem.items.reduce(
  //   (sum, item) => sum + (item.metadata.word_count || 0), 0
  // );

  // Calculate total code examples count from metadata
  // const totalCodeExamples = useMemo(() => {
  //   return groupedItem.items.reduce(
  //     (sum, item) => sum + (item.metadata.code_examples_count || 0),
  //     0,
  //   );
  // }, [groupedItem.items]);

  // Calculate active item's code examples count from metadata
  const activeCodeExamples = activeItem.code_examples?.length || 0;

  // Calculate active item's word count
  const activeWordCount = activeItem.metadata.word_count || 0;

  // Get code examples from all items in the group
  // const allCodeExamples = useMemo(() => {
  //   return groupedItem.items.reduce(
  //     (examples, item) => {
  //       const itemExamples = item.code_examples || [];
  //       return [...examples, ...itemExamples.map((ex: any, idx: number) => ({
  //         title: ex.metadata?.example_name || ex.metadata?.title || ex.summary?.split('\n')[0] || 'Code Example',
  //         description: ex.summary || '',
  //       }))];
  //     },
  //     [] as Array<{
  //       title: string;
  //       description: string;
  //     }>,
  //   );
  // }, [groupedItem.items]);

  // Format code examples for the modal with additional safety checks
  const formattedCodeExamples = useMemo(() => {
    return groupedItem.items.reduce((examples: CodeExample[], item) => {
      if (!item || !item.code_examples) return examples;

      const itemExamples = item.code_examples.map(
        (example: any, index: number) => ({
          id: example.id || `${item.id || "unknown"}-example-${index}`,
          title:
            example.metadata?.example_name ||
            example.metadata?.title ||
            example.summary?.split("\n")[0] ||
            "Code Example",
          description: example.summary || "No description available",
          language:
            example.metadata?.language ||
            guessLanguageFromTitle(example.metadata?.title || ""),
          code:
            example.content ||
            example.metadata?.code ||
            "// Code example not available",
          tags: example.metadata?.tags || [],
        })
      );

      return [...examples, ...itemExamples];
    }, []);
  }, [groupedItem.items]);

  // Function to shuffle to the next card
  const shuffleToNextCard = () => {
    if (!isGrouped || isShuffling) return;

    setIsShuffling(true);
    const nextIndex = (activeCardIndex + 1) % groupedItem.items.length;

    // Add a small delay to allow animation to complete
    setTimeout(() => {
      setActiveCardIndex(nextIndex);
      setIsShuffling(false);
    }, 300);
  };

  // Card content renderer - extracted to avoid duplication
  const renderCardContent = (item = activeItem) => (
    <div className="relative z-10 flex flex-col h-full">
      {/* Header section - fixed height */}
      <div className="flex items-center gap-2 mb-3 card-3d-layer-1">
        {/* Source type icon */}
        {item.metadata.source_type === "url" ? (
          <LinkIcon className={`w-4 h-4 ${getSourceIconColor(item)}`} />
        ) : (
          <Upload className={`w-4 h-4 ${getSourceIconColor(item)}`} />
        )}
        {/* Knowledge type icon */}
        {item.metadata.knowledge_type === "technical" ? (
          <BoxIcon className={`w-4 h-4 ${getTypeIconColor(item)}`} />
        ) : (
          <Brain className={`w-4 h-4 ${getTypeIconColor(item)}`} />
        )}
        {/* Title with source count badge moved to header */}
        <div className="flex items-center flex-1 gap-2 min-w-0">
          <h3 className="text-gray-800 dark:text-white font-medium flex-1 line-clamp-1 truncate min-w-0">
            {item.title || groupedItem.domain}
          </h3>
          {/* Sources badge - moved to header */}
          {isGrouped && (
            <button
              onClick={shuffleToNextCard}
              className="group flex items-center gap-1 px-2 py-1 bg-blue-500/20 border border-blue-500/40 rounded-full backdrop-blur-sm shadow-[0_0_15px_rgba(0,0,0,0.1)] hover:shadow-[0_0_20px_rgba(0,0,0,0.15)] transition-all duration-300 card-3d-layer-3 flex-shrink-0"
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
            >
              <Globe className="w-3 h-3 text-blue-400" />
              <span className="text-xs text-blue-400 font-medium">
                {activeCardIndex + 1}/{groupedItem.items.length}
              </span>
              <ChevronRight className="w-3 h-3 text-blue-400 group-hover:translate-x-0.5 transition-transform" />
            </button>
          )}
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowEditModal(true);
            }}
            className="p-1 text-gray-500 hover:text-blue-500"
            title="Edit"
          >
            <Pencil className="w-3 h-3" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowDeleteConfirm(true);
            }}
            className="p-1 text-gray-500 hover:text-red-500"
            title="Delete"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Description section - fixed height */}
      <p className="text-gray-600 dark:text-zinc-400 text-sm mb-3 line-clamp-2 card-3d-layer-2">
        {item.metadata.description ||
          (groupedItem.items.length === 1
            ? `Content from ${groupedItem.domain}`
            : `Source ${activeCardIndex + 1} of ${
                groupedItem.items.length
              } from ${groupedItem.domain}`)}
      </p>

      {/* Tags section - flexible height with flex-1 */}
      <div className="flex-1 flex flex-col card-3d-layer-2 min-h-[4rem]">
        <TagsDisplay tags={item.metadata.tags || []} />
      </div>

      {/* Footer section - anchored to bottom */}
      <div className="flex items-end justify-between mt-auto card-3d-layer-1">
        {/* Left side - refresh button and updated stacked */}
        <div className="flex flex-col">
          {item.metadata.source_type === "url" && (
            <button
              onClick={handleRefresh}
              className={`flex items-center gap-1 mb-1 px-2 py-1 transition-colors ${
                item.metadata.knowledge_type === "technical"
                  ? "text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300"
                  : "text-cyan-500 hover:text-cyan-600 dark:text-cyan-400 dark:hover:text-cyan-300"
              }`}
              title={`Refresh from: ${
                item.metadata.original_url || item.url || "URL not available"
              }`}
            >
              <RefreshCw className="w-3 h-3" />
              <span className="text-sm font-medium">Recrawl</span>
            </button>
          )}
          <span className="text-xs text-gray-500 dark:text-zinc-500">
            Updated: {new Date(groupedItem.updated_at).toLocaleDateString()}
          </span>
        </div>

        {/* Right side - code examples and status inline */}
        <div className="flex items-center gap-2">
          {/* Code examples badge - updated colors */}
          {activeCodeExamples > 0 && (
            <div
              className="cursor-pointer relative card-3d-layer-3"
              onClick={() => setShowCodeModal(true)}
              onMouseEnter={() => setShowCodeTooltip(true)}
              onMouseLeave={() => setShowCodeTooltip(false)}
            >
              <div
                className={`flex items-center gap-1 px-2 py-1 rounded-full backdrop-blur-sm transition-all duration-300 ${
                  item.metadata.source_type === "url"
                    ? item.metadata.knowledge_type === "technical"
                      ? "bg-blue-500/20 border border-blue-500/40 shadow-[0_0_15px_rgba(59,130,246,0.3)] hover:shadow-[0_0_20px_rgba(59,130,246,0.5)]"
                      : "bg-cyan-500/20 border border-cyan-500/40 shadow-[0_0_15px_rgba(34,211,238,0.3)] hover:shadow-[0_0_20px_rgba(34,211,238,0.5)]"
                    : item.metadata.knowledge_type === "technical"
                    ? "bg-purple-500/20 border border-purple-500/40 shadow-[0_0_15px_rgba(168,85,247,0.3)] hover:shadow-[0_0_20px_rgba(168,85,247,0.5)]"
                    : "bg-pink-500/20 border border-pink-500/40 shadow-[0_0_15px_rgba(236,72,153,0.3)] hover:shadow-[0_0_20px_rgba(236,72,153,0.5)]"
                }`}
              >
                <Code
                  className={`w-3 h-3 ${
                    item.metadata.source_type === "url"
                      ? item.metadata.knowledge_type === "technical"
                        ? "text-blue-400"
                        : "text-cyan-400"
                      : item.metadata.knowledge_type === "technical"
                      ? "text-purple-400"
                      : "text-pink-400"
                  }`}
                />
                <span
                  className={`text-xs font-medium ${
                    item.metadata.source_type === "url"
                      ? item.metadata.knowledge_type === "technical"
                        ? "text-blue-400"
                        : "text-cyan-400"
                      : item.metadata.knowledge_type === "technical"
                      ? "text-purple-400"
                      : "text-pink-400"
                  }`}
                >
                  {activeCodeExamples}
                </span>
              </div>
              {/* Code Examples Tooltip - positioned relative to the badge */}
              {showCodeTooltip && (
                <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-black dark:bg-zinc-800 text-white text-xs rounded-lg py-2 px-3 shadow-lg z-50 whitespace-nowrap">
                  <div className="font-medium">
                    Click to view Stored Code Examples
                  </div>
                  <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-black dark:border-t-zinc-800"></div>
                </div>
              )}
            </div>
          )}

          {/* Page count - orange neon container */}
          <div
            className="relative card-3d-layer-3"
            onMouseEnter={() => setShowPageTooltip(true)}
            onMouseLeave={() => setShowPageTooltip(false)}
          >
            <div className="flex items-center gap-1 px-2 py-1 bg-orange-500/20 border border-orange-500/40 rounded-full backdrop-blur-sm shadow-[0_0_15px_rgba(251,146,60,0.3)] transition-all duration-300">
              <FileText className="w-3 h-3 text-orange-400" />
              <span className="text-xs text-orange-400 font-medium">
                {Math.ceil(activeWordCount / 250).toLocaleString()}
              </span>
            </div>
            {/* Page count tooltip - positioned relative to the badge */}
            {showPageTooltip && (
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 bg-black dark:bg-zinc-800 text-white text-xs px-3 py-2 rounded-lg shadow-lg z-50 whitespace-nowrap">
                <div className="font-medium mb-1">
                  {activeWordCount.toLocaleString()} words
                </div>
                <div className="text-gray-300 space-y-0.5">
                  <div>
                    = {Math.ceil(activeWordCount / 250).toLocaleString()} pages
                  </div>
                  <div>
                    = {(activeWordCount / 80000).toFixed(1)} average novels
                  </div>
                </div>
                <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-black dark:border-t-zinc-800"></div>
              </div>
            )}
          </div>

          <Badge
            color={statusColorMap[item.metadata.status || "active"] as any}
            className="card-3d-layer-2"
          >
            {(item.metadata.status || "active").charAt(0).toUpperCase() +
              (item.metadata.status || "active").slice(1)}
          </Badge>
        </div>
      </div>
    </div>
  );

  return (
    <div
      ref={cardRef}
      className={`relative h-full ${isRemoving ? "card-removing" : ""}`}
      style={{
        transform: isGrouped ? "perspective(1200px)" : tiltStyles.transform,
        transition: tiltStyles.transition,
        transformStyle: "preserve-3d",
      }}
      {...tiltHandlers}
    >
      {/* Stacked cards effect - background cards */}
      {isGrouped && (
        <>
          {/* Third card (bottom of stack) */}
          <div
            className="absolute top-0 left-0 w-full h-full"
            style={{
              zIndex: 1,
              transform:
                "translateZ(-60px) translateY(-16px) translateX(-8px) rotateX(-2deg) rotateY(-2deg)",
              transformStyle: "preserve-3d",
              filter: "drop-shadow(0 10px 8px rgba(0, 0, 0, 0.15))",
            }}
          >
            <Card
              accentColor={getCardColor(
                groupedItem.items[
                  (activeCardIndex + groupedItem.items.length - 2) %
                    groupedItem.items.length
                ]
              )}
              className="w-full h-full bg-white/60 dark:bg-zinc-900/60 backdrop-blur-md shadow-md opacity-60 overflow-hidden"
            >
              {/* Add a simplified version of the content for depth */}
              <div className="p-4 opacity-30">
                {renderCardContent(
                  groupedItem.items[
                    (activeCardIndex + groupedItem.items.length - 2) %
                      groupedItem.items.length
                  ]
                )}
              </div>
            </Card>
          </div>

          {/* Second card (middle of stack) */}
          <div
            className="absolute top-0 left-0 w-full h-full"
            style={{
              zIndex: 2,
              transform:
                "translateZ(-30px) translateY(-8px) translateX(-4px) rotateX(-1deg) rotateY(-1deg)",
              transformStyle: "preserve-3d",
              filter: "drop-shadow(0 8px 6px rgba(0, 0, 0, 0.1))",
            }}
          >
            <Card
              accentColor={getCardColor(
                groupedItem.items[
                  (activeCardIndex + groupedItem.items.length - 1) %
                    groupedItem.items.length
                ]
              )}
              className="w-full h-full bg-white/70 dark:bg-zinc-900/70 backdrop-blur-md shadow-md opacity-80 overflow-hidden"
            >
              {/* Add a simplified version of the content for depth */}
              <div className="p-4 opacity-60">
                {renderCardContent(
                  groupedItem.items[
                    (activeCardIndex + groupedItem.items.length - 1) %
                      groupedItem.items.length
                  ]
                )}
              </div>
            </Card>
          </div>
        </>
      )}

      {/* Main card (top of stack) - with animation for shuffling */}
      <div
        className={`relative z-10 transition-all duration-300 h-full ${
          isShuffling ? "animate-card-shuffle-out" : "opacity-100 scale-100"
        }`}
        style={{
          transform: "translateZ(0)",
          transformStyle: "preserve-3d",
          filter: "drop-shadow(0 4px 3px rgba(0, 0, 0, 0.07))",
        }}
      >
        <Card
          accentColor={accentColor}
          className="relative h-full flex flex-col backdrop-blur-lg bg-white/80 dark:bg-zinc-900/80"
        >
          {/* Reflection overlay */}
          <div
            className="card-reflection"
            style={{
              opacity: isGrouped ? 0 : tiltStyles.reflectionOpacity,
              backgroundPosition: tiltStyles.reflectionPosition,
            }}
          ></div>

          {/* Card content */}
          {renderCardContent()}
        </Card>
      </div>

      {/* Incoming card animation - only visible during shuffle */}
      {isShuffling && (
        <div
          className="absolute inset-0 z-20 animate-card-shuffle-in"
          style={{
            transform: "translateZ(30px)",
            transformStyle: "preserve-3d",
            filter: "drop-shadow(0 4px 3px rgba(0, 0, 0, 0.07))",
          }}
        >
          <Card
            accentColor={accentColor}
            className="relative h-full flex flex-col backdrop-blur-lg bg-white/80 dark:bg-zinc-900/80"
          >
            {/* Reflection overlay */}
            <div
              className="card-reflection"
              style={{
                opacity: isGrouped ? 0 : tiltStyles.reflectionOpacity,
                backgroundPosition: tiltStyles.reflectionPosition,
              }}
            ></div>

            {/* Card content for next item */}
            {renderCardContent(
              groupedItem.items[
                (activeCardIndex + 1) % groupedItem.items.length
              ]
            )}
          </Card>
        </div>
      )}

      {/* Sources tooltip */}
      {showTooltip && isGrouped && (
        <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-black/90 dark:bg-zinc-800/90 backdrop-blur-md text-white text-xs rounded-lg py-2 px-3 shadow-lg z-50 whitespace-nowrap max-w-xs">
          <div className="font-semibold text-blue-300 mb-1">
            Grouped Sources:
          </div>
          {groupedItem.items.map((item, index) => (
            <div
              key={index}
              className={`text-gray-300 ${
                activeCardIndex === index ? "text-blue-300 font-medium" : ""
              }`}
            >
              {index + 1}. {item.title}
            </div>
          ))}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-black dark:border-t-zinc-800"></div>
        </div>
      )}

      {/* Code Examples Modal */}
      {showCodeModal && formattedCodeExamples.length > 0 && (
        <CodeViewerModal
          examples={formattedCodeExamples}
          onClose={() => setShowCodeModal(false)}
        />
      )}

      {/* Delete Confirm Modal */}
      {showDeleteConfirm && (
        <DeleteConfirmModal
          onConfirm={handleDelete}
          onCancel={() => setShowDeleteConfirm(false)}
          title={isGrouped ? "Delete Grouped Sources" : "Delete Knowledge Item"}
          message={
            isGrouped
              ? `Are you sure you want to delete all ${groupedItem.items.length} sources from ${groupedItem.domain}? This action cannot be undone.`
              : "Are you sure you want to delete this knowledge item? This action cannot be undone."
          }
        />
      )}

      {/* Edit Modal - edits the active item */}
      {showEditModal && activeItem && (
        <EditKnowledgeItemModal
          item={activeItem}
          onClose={() => setShowEditModal(false)}
          onUpdate={() => {
            if (onUpdate) onUpdate();
          }}
        />
      )}
    </div>
  );
};
