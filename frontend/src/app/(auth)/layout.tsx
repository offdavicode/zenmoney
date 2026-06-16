export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <main className="flex min-h-screen w-full animate-fade-in">
      
      <img className=" hidden lg:flex w-2/3 bg-surface-hover flex-col items-center justify-center relative overflow-hidden object-cover " src="hero.png" alt="" />

      
      <div className="flex w-full lg:w-1/2 items-center justify-center p-6 sm:p-12 bg-background">
        <div className="w-full max-w-md animate-slide-up">
          {children}
        </div>
      </div>
    </main>
  );
}
