import Image from "next/image";

export function SharedLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-gray-50">
      <div className="absolute right-0 bottom-0 h-[285px] w-[503px] opacity-90">
        <Image
          src="/brain-visualization.png"
          alt=""
          fill
          className="object-cover object-bottom-right"
          priority
        />
      </div>

      <div className="relative z-10 mx-auto mt-5 flex h-screen w-screen flex-col items-center justify-center md:mt-0">
        <div className="fixed top-6 left-10 md:mb-6">
          <div className="text-primary-9 w-10 h-10">OpenBrainInstitute</div>
        </div>
        {children}
      </div>
    </div>
  );
}
