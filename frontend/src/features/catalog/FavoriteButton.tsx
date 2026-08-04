import { Heart } from "lucide-react";
import { useFavorites } from "@/hooks/useFavorites";
import { cn } from "@/lib/cn";

export function FavoriteButton({
  cardUuid,
  size = "md",
  className,
}: {
  cardUuid: string;
  size?: "sm" | "md";
  className?: string;
}) {
  const { isFavorite, toggle } = useFavorites();
  const fav = isFavorite(cardUuid);
  const px = size === "sm" ? "h-4 w-4" : "h-5 w-5";

  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation();
        e.preventDefault();
        void toggle(cardUuid);
      }}
      aria-pressed={fav}
      aria-label={fav ? "Remover dos favoritos" : "Favoritar carta"}
      title={fav ? "Favoritada" : "Favoritar"}
      className={cn(
        "grid place-items-center rounded-[4px] border-2 border-[var(--color-border)] bg-black/40 p-1 transition-colors",
        fav ? "text-[var(--color-danger)]" : "text-white/70 hover:text-white",
        className,
      )}
    >
      <Heart className={px} fill={fav ? "currentColor" : "none"} />
    </button>
  );
}
