"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { ConnectWalletButton } from "@/components/web3/ConnectWalletButton";
import { useSidebar } from "@/lib/sidebar-context";
import { useBackendStatus } from "@/hooks/useBackendStatus";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

const NAV_ITEMS = [
	{ title: "Vault", href: "/dashboard/vault", icon: "savings" },
	{ title: "Scan", href: "/dashboard/scan", icon: "radar" },
	{ title: "Activity", href: "/dashboard/portfolio", icon: "history" },
	{ title: "Explore", href: "/dashboard/simulation", icon: "travel_explore" },
	{ title: "Research", href: "/dashboard/research", icon: "science" },
	{ title: "Proof", href: "/dashboard/leaderboard", icon: "verified" },
];

export function Sidebar() {
	const pathname = usePathname();
	const { isOpen } = useSidebar();
	const backendStatus = useBackendStatus();

	return (
		<>
			<aside
				className={cn(
					"hidden md:flex h-screen flex-col py-10 gap-8 shrink-0 relative z-50 border-r border-border/50 bg-background transition-all",
					isOpen ? "w-72 px-6" : "w-18 px-3 items-center"
				)}
				style={{
					transition:
						"width 300ms cubic-bezier(0.4, 0, 0.2, 1), padding 300ms cubic-bezier(0.4, 0, 0.2, 1)",
				}}
			>
				{/* Backend Status Gradient Indicator - Top Bar */}
				<div
					className="absolute top-0 left-0 right-0 h-1 transition-all duration-500"
					style={{
						background:
							backendStatus === "online"
								? "linear-gradient(90deg, rgba(34,197,94,0.6) 0%, rgba(34,197,94,0.3) 100%)"
								: backendStatus === "offline"
								? "linear-gradient(90deg, rgba(239,68,68,0.6) 0%, rgba(239,68,68,0.3) 100%)"
								: "linear-gradient(90deg, rgba(156,163,175,0.4) 0%, rgba(156,163,175,0.2) 100%)",
					}}
				/>

				{/* Ambient lighting */}
				<div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-primary/5 to-transparent pointer-events-none" />

				{/* Logo */}
				<Link
					href="/"
					className={cn(
						"flex items-center group",
						isOpen ? "gap-4 px-2" : "justify-center"
					)}
				>
					<div className="relative w-10 h-10 shrink-0 rounded-full overflow-hidden flex items-center justify-center transition-transform duration-500 group-hover:scale-105">
						<Image
							src="/signal_logo.svg"
							alt="Signals Logo"
							fill
							className="object-cover"
						/>
					</div>
					<div
						className={cn(
							"transition-all duration-300 overflow-hidden whitespace-nowrap",
							!isOpen && "w-0 opacity-0"
						)}
					>
						<h1
							className="text-[1.35rem] font-bold text-foreground tracking-tighter"
							style={{ fontFamily: "var(--font-space)" }}
						>
							Signals
						</h1>
						<p className="text-[9px] uppercase tracking-[0.2em] font-semibold text-muted-foreground mt-0.5 group-hover:text-foreground/80 transition-colors">
							Web3 Intelligence
						</p>
					</div>
				</Link>

				{/* Main nav */}
				<nav className="flex flex-col gap-2 mt-6">
					{NAV_ITEMS.map((item) => {
						const isActive =
							pathname === item.href ||
							(item.href !== "/dashboard" && pathname?.startsWith(item.href));

						const navLink = (
							<Link
								href={item.href}
								className={cn(
									"relative rounded-xl py-3.5 flex items-center text-[13px] font-medium tracking-wide transition-all ease-out duration-300 group overflow-hidden cursor-pointer",
									isOpen ? "px-4 gap-4" : "justify-center w-12 h-12",
									isActive
										? "text-primary"
										: "text-muted-foreground hover:text-foreground hover:bg-black/5 dark:hover:bg-white/5"
								)}
							>
								{isActive && (
									<div className="absolute inset-0 bg-primary/10 transition-transform" />
								)}
								{isActive && isOpen && (
									<div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.75 h-1/2 rounded-r-full bg-primary" />
								)}
								<span
									className={cn(
										"material-symbols-outlined relative z-10 transition-transform duration-300",
										!isActive && "group-hover:scale-110",
										isActive && "[font-variation-settings:'FILL'1]"
									)}
									style={{ fontSize: "1.3rem" }}
								>
									{item.icon}
								</span>
								<span
									className={cn(
										"relative z-10 transition-all duration-300 whitespace-nowrap",
										!isOpen && "hidden"
									)}
									style={{
										fontFamily: isActive ? "var(--font-space)" : "inherit",
									}}
								>
									{item.title}
								</span>
							</Link>
						);

						return !isOpen ? (
							<Tooltip key={item.href}>
								<TooltipTrigger asChild>{navLink}</TooltipTrigger>
								<TooltipContent side="right" className="text-xs font-medium">
									{item.title}
								</TooltipContent>
							</Tooltip>
						) : (
							<div key={item.href}>{navLink}</div>
						);
					})}
				</nav>

				{/* Bottom section */}
				<div className="mt-auto flex flex-col gap-2 relative z-10 w-full items-center">
					<div
						className={cn(
							"mb-6 hover:scale-[1.02] transition-transform duration-300",
							!isOpen && "!h-0 !mb-0 overflow-hidden p-0"
						)}
					>
						<ConnectWalletButton />
					</div>

					<div className="w-full h-px bg-border/50 mb-2" />

					{!isOpen ? (
						<Tooltip>
							<TooltipTrigger asChild>
								<Link
									href="/dashboard/settings"
									className="text-muted-foreground hover:text-foreground rounded-xl py-3 flex items-center text-xs font-medium tracking-wide transition-colors group cursor-pointer justify-center w-12 h-12"
								>
									<span
										className="material-symbols-outlined group-hover:rotate-45 transition-transform duration-500 shrink-0"
										style={{ fontSize: "1.2rem" }}
									>
										settings
									</span>
								</Link>
							</TooltipTrigger>
							<TooltipContent side="right" className="text-xs font-medium">
								Settings
							</TooltipContent>
						</Tooltip>
					) : (
						<Link
							href="/dashboard/settings"
							className="text-muted-foreground hover:text-foreground rounded-xl py-3 flex items-center text-xs font-medium tracking-wide transition-colors group cursor-pointer px-4 gap-4 w-full"
						>
							<span
								className="material-symbols-outlined group-hover:rotate-45 transition-transform duration-500 shrink-0"
								style={{ fontSize: "1.2rem" }}
							>
								settings
							</span>
							<span className="transition-all duration-300 whitespace-nowrap">
								Settings
							</span>
						</Link>
					)}
					{!isOpen ? (
						<Tooltip>
							<TooltipTrigger asChild>
								<Link
									href="#"
									className="text-muted-foreground hover:text-foreground rounded-xl py-3 flex items-center text-xs font-medium tracking-wide transition-colors group cursor-pointer justify-center w-12 h-12"
								>
									<span
										className="material-symbols-outlined group-hover:scale-110 transition-transform duration-300 shrink-0"
										style={{ fontSize: "1.2rem" }}
									>
										help_outline
									</span>
								</Link>
							</TooltipTrigger>
							<TooltipContent side="right" className="text-xs font-medium">
								Support
							</TooltipContent>
						</Tooltip>
					) : (
						<Link
							href="#"
							className="text-muted-foreground hover:text-foreground rounded-xl py-3 flex items-center text-xs font-medium tracking-wide transition-colors group cursor-pointer px-4 gap-4 w-full"
						>
							<span
								className="material-symbols-outlined group-hover:scale-110 transition-transform duration-300 shrink-0"
								style={{ fontSize: "1.2rem" }}
							>
								help_outline
							</span>
							<span className="transition-all duration-300 whitespace-nowrap">
								Support
							</span>
						</Link>
					)}
				</div>
			</aside>

			{/* Mobile bottom nav */}
			<nav
				className="md:hidden fixed bottom-0 left-0 right-0 h-[4.5rem] flex justify-around items-center px-4 border-t border-border/50 bg-background/85 backdrop-blur-xl z-[100]"
			>
				{NAV_ITEMS.map((item) => {
					const isActive =
						pathname === item.href ||
						(pathname?.startsWith(item.href) ?? false);
					return (
						<Link
							key={item.href}
							href={item.href}
							className="flex flex-col items-center gap-1.5 p-2 rounded-xl active:scale-95 transition-transform cursor-pointer"
						>
							<span
								className="material-symbols-outlined transition-colors duration-300"
								style={{
									fontSize: "1.4rem",
									color: isActive ? "var(--primary)" : "#737373",
									fontVariationSettings: isActive ? "'FILL' 1" : "'FILL' 0",
								}}
							>
								{item.icon}
							</span>
							<span
								className="text-[9px] font-bold uppercase tracking-wider"
								style={{
									color: isActive ? "var(--primary)" : "#737373",
									fontFamily: "var(--font-space)",
								}}
							>
								{item.title}
							</span>
						</Link>
					);
				})}
			</nav>
		</>
	);
}
