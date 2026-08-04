import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button, Input, Panel, useToast } from "@/components/ui";
import { useAuth } from "@/hooks/useAuth";
import { apiErrorMessage } from "@/lib/api";

const schema = z.object({
  email: z.string().email("E-mail inválido"),
  password: z.string().min(1, "Informe sua senha"),
});
type FormData = z.infer<typeof schema>;

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();
  const [submitting, setSubmitting] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    setSubmitting(true);
    try {
      await login(data.email, data.password);
      const to = (location.state as { from?: { pathname: string } })?.from?.pathname ?? "/app";
      navigate(to, { replace: true });
    } catch (e) {
      toast.error("Não foi possível entrar", apiErrorMessage(e, "Credenciais inválidas."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="grid min-h-dvh place-items-center px-4">
      <div className="w-full max-w-sm">
        <Link to="/" className="mb-6 flex items-center justify-center gap-2">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-brand-500 font-display font-bold text-white">
            R
          </span>
          <span className="font-display text-xl font-bold">RideDeck</span>
        </Link>
        <Panel className="p-6">
          <h1 className="font-display text-2xl font-bold">Entrar</h1>
          <p className="mt-1 text-sm text-[var(--color-ink-muted)]">Bem-vindo de volta, cardfighter.</p>
          <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4" noValidate>
            <Input label="E-mail" type="email" autoComplete="email" error={errors.email?.message} {...register("email")} />
            <Input
              label="Senha"
              type="password"
              autoComplete="current-password"
              error={errors.password?.message}
              {...register("password")}
            />
            <Button type="submit" className="w-full" loading={submitting}>
              Entrar
            </Button>
          </form>
          <p className="mt-5 text-center text-sm text-[var(--color-ink-muted)]">
            Não tem conta?{" "}
            <Link to="/register" className="font-semibold text-[var(--color-accent)] hover:underline">
              Criar conta
            </Link>
          </p>
        </Panel>
      </div>
    </div>
  );
}
