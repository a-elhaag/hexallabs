import { PrismaClient } from "../generated/prisma";

const prisma = new PrismaClient();

const tiers = [
  {
    name: "core",
    displayName: "Core",
    monthlyPriceUsd: 0,
    monthlyUsageUsd: 5,
    weeklyUsageUsd: 1.25,
    rolloverPct: 0.5,
    maxModels: 2,
    active: true,
    sortOrder: 0,
  },
  {
    name: "elite",
    displayName: "Elite",
    monthlyPriceUsd: 15,
    monthlyUsageUsd: 10,
    weeklyUsageUsd: 2.5,
    rolloverPct: 0.5,
    maxModels: 7,
    active: true,
    sortOrder: 1,
  },
  {
    name: "arch",
    displayName: "Arch",
    monthlyPriceUsd: 29,
    monthlyUsageUsd: 20,
    weeklyUsageUsd: 5,
    rolloverPct: 0.5,
    maxModels: 7,
    active: false, // not yet launched
    sortOrder: 2,
  },
];

async function main() {
  console.log("Seeding pricing tiers...");

  for (const tier of tiers) {
    const result = await prisma.pricingTier.upsert({
      where: { name: tier.name },
      update: tier,
      create: tier,
    });
    console.log(`  ${result.displayName} (${result.name}) — $${result.monthlyPriceUsd}/mo, $${result.monthlyUsageUsd} usage`);
  }

  console.log("Done.");
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
