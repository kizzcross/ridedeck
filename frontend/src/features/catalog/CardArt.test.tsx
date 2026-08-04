import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { CardArt } from "./CardArt";
import type { CardListItem } from "@/api/cards";

const baseCard: CardListItem = {
  uuid: "u1",
  name: "Blazing Dragon #16",
  slug: "blazing-dragon-16",
  grade: 3,
  power: 13000,
  shield: 0,
  critical: 1,
  card_type: "normal_unit",
  trigger: "",
  nation: "dragon_empire",
  clan: "",
  is_persona_ride: false,
  default_printing: { uuid: "p1", card_number: "X-1", rarity: "RRR", image_url: "", price: "5.00" },
};

describe("CardArt", () => {
  it("renders a placeholder face when there is no image", () => {
    render(<CardArt card={baseCard} />);
    expect(screen.getByText("Blazing Dragon #16")).toBeInTheDocument();
    expect(screen.getByText("13,000")).toBeInTheDocument();
    expect(screen.getByText("Dragon Empire")).toBeInTheDocument();
  });

  it("shows the trigger tag for trigger cards", () => {
    render(<CardArt card={{ ...baseCard, grade: 0, trigger: "critical" }} />);
    expect(screen.getByText("critical")).toBeInTheDocument();
  });
});
