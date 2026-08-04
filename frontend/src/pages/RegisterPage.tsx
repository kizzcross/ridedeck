import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button, Input, Panel, useToast } from "@/components/ui";
import { useAuth } from "@/hooks/useAuth";
import { apiErrorMessage } from "@/lib/api";

const schema = z
  .object({
    username: z
      .string()
      .min(3, "Mínimo 3 caracteres")
      .max(32, "Máximo 32 caracteres")
      .regex(/^[a-zA-Z0-9_]+$/, "Apenas letras, números e _"),
    email: z.string().email("E-mail inválido"),
    password: z.string().min(8, "Mínimo 8 caracteres"),
    password_confirm: z.string(),
  })
  .refine((d) => d.password === d.password_confirm, {
    message: "As senhas não coincidem",
    path: ["password_confirm"],
  });
type FormData = z.infer<typeof schema>;

export function RegisterPage() {
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();
  const [searchParams] = useSearchParams();
  const referralCode = searchParams.get("ref") ?? "";
  const [submitting, setSubmitting] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    setSubmitting(true);
    try {
      await registerUser({ ...data, referral_code: referralCode });
      toast.success("Conta criada!", referralCode ? "Você já entrou com um amigo!" : "Bem-vindo ao RideDeck.");
      navigate("/app", { replace: true });
    } catch (e) {
      toast.error("Não foi possível criar a conta", apiErrorMessage(e));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="grid min-h-dvh place-items-center px-4 py-8">
      <div className="w-full max-w-sm">
        <Link to="/" className="mb-6 flex items-center justify-center gap-2">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-brand-500 font-display font-bold text-white">
            R
          </span>
          <span className="font-display text-xl font-bold">RideDeck</span>
        </Link>
        <Panel className="p-6">
          <h1 className="font-display text-2xl font-bold">Criar conta</h1>
          <p className="mt-1 text-sm text-[var(--color-ink-muted)]">Grátis. Comece a montar decks em segundos.</p>
          {referralCode && (
            <div className="mt-3 rounded-[var(--radius-card)] border-2 border-[var(--color-accent)]/50 bg-[var(--color-accent)]/10 px-3 py-2 text-xs text-[var(--color-ink)]">
              🎟️ Você foi convidado (código <b>{referralCode}</b>) — já entrará como amigo de quem te convidou.
            </div>
          )}
          <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4" noValidate>
            <Input label="Nome de usuário" autoComplete="username" error={errors.username?.message} {...register("username")} />
            <Input label="E-mail" type="email" autoComplete="email" error={errors.email?.message} {...register("email")} />
            <Input
              label="Senha"
              type="password"
              autoComplete="new-password"
              error={errors.password?.message}
              {...register("password")}
            />
            <Input
              label="Confirmar senha"
              type="password"
              autoComplete="new-password"
              error={errors.password_confirm?.message}
              {...register("password_confirm")}
            />
            <Button type="submit" className="w-full" loading={submitting}>
              Criar conta
            </Button>
          </form>
          <p className="mt-5 text-center text-sm text-[var(--color-ink-muted)]">
            Já tem conta?{" "}
            <Link to="/login" className="font-semibold text-[var(--color-accent)] hover:underline">
              Entrar
            </Link>
          </p>
        </Panel>
      </div>
    </div>
  );
}
