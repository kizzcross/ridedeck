import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Button } from "./Button";

describe("Button", () => {
  it("renders its label and handles clicks", async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Adicionar carta</Button>);
    await userEvent.click(screen.getByRole("button", { name: "Adicionar carta" }));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("is disabled and does not fire while loading", async () => {
    const onClick = vi.fn();
    render(
      <Button loading onClick={onClick}>
        Salvando
      </Button>,
    );
    const btn = screen.getByRole("button");
    expect(btn).toBeDisabled();
    await userEvent.click(btn);
    expect(onClick).not.toHaveBeenCalled();
  });
});
