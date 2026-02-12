"""Fee and profit calculations for each resale platform."""

from dataclasses import dataclass

from app.config import get_settings

settings = get_settings()

# MacBid fee constants
MACBID_BUYER_PREMIUM = 0.15
MACBID_LOT_FEE = 3.00

# eBay fee constants
EBAY_FVF_RATE = 0.136  # 13.6% final value fee
EBAY_PER_ORDER_FEE = 0.40

# Amazon referral fee rates by category (simplified)
AMAZON_FEE_RATES = {
    "Electronics": 0.08,
    "Computers": 0.08,
    "Video Games": 0.15,
    "Home & Kitchen": 0.15,
    "Toys & Games": 0.15,
    "Clothing": 0.17,
    "Beauty": 0.08,
    "Health": 0.08,
    "Sports": 0.15,
    "Tools": 0.12,
    "default": 0.15,
}

# Average FBA fees by size tier (simplified estimates)
FBA_SMALL_STANDARD = 3.22
FBA_LARGE_STANDARD = 5.50


@dataclass
class CostBreakdown:
    winning_bid: float
    buyer_premium: float
    lot_fee: float
    tax: float
    total_cost: float


@dataclass
class RevenueBreakdown:
    sell_price: float
    platform_fees: float
    shipping_cost: float
    net_revenue: float


@dataclass
class ProfitResult:
    cost: CostBreakdown
    revenue: RevenueBreakdown
    profit: float
    roi_pct: float


def calculate_macbid_cost(
    winning_bid: float,
    tax_rate: float | None = None,
) -> CostBreakdown:
    """Calculate total MacBid purchase cost.

    Total = winning_bid + (winning_bid * 15%) + $3.00 lot fee + tax
    Tax is applied to (winning_bid + buyer_premium).
    """
    if tax_rate is None:
        tax_rate = settings.default_tax_rate

    buyer_premium = winning_bid * MACBID_BUYER_PREMIUM
    taxable = winning_bid + buyer_premium
    tax = taxable * tax_rate
    total = winning_bid + buyer_premium + MACBID_LOT_FEE + tax

    return CostBreakdown(
        winning_bid=winning_bid,
        buyer_premium=round(buyer_premium, 2),
        lot_fee=MACBID_LOT_FEE,
        tax=round(tax, 2),
        total_cost=round(total, 2),
    )


def calculate_ebay_revenue(
    sell_price: float,
    shipping_cost: float = 0.0,
) -> RevenueBreakdown:
    """Calculate eBay net revenue after fees.

    Fees: 13.6% FVF + $0.40 per order.
    """
    fvf = sell_price * EBAY_FVF_RATE
    total_fees = fvf + EBAY_PER_ORDER_FEE
    net = sell_price - total_fees - shipping_cost

    return RevenueBreakdown(
        sell_price=sell_price,
        platform_fees=round(total_fees, 2),
        shipping_cost=shipping_cost,
        net_revenue=round(net, 2),
    )


def calculate_amazon_revenue(
    sell_price: float,
    category: str = "default",
    use_fba: bool = True,
    is_large: bool = False,
    shipping_cost: float = 0.0,
) -> RevenueBreakdown:
    """Calculate Amazon net revenue after fees.

    Fees: category referral fee + FBA fee (if applicable).
    """
    fee_rate = AMAZON_FEE_RATES.get(category, AMAZON_FEE_RATES["default"])
    referral_fee = sell_price * fee_rate

    fba_fee = 0.0
    if use_fba:
        fba_fee = FBA_LARGE_STANDARD if is_large else FBA_SMALL_STANDARD

    total_fees = referral_fee + fba_fee
    net = sell_price - total_fees - shipping_cost

    return RevenueBreakdown(
        sell_price=sell_price,
        platform_fees=round(total_fees, 2),
        shipping_cost=shipping_cost,
        net_revenue=round(net, 2),
    )


def calculate_profit(
    winning_bid: float,
    sell_price: float,
    platform: str,
    category: str = "default",
    shipping_cost: float = 0.0,
    tax_rate: float | None = None,
    use_fba: bool = True,
    is_large: bool = False,
) -> ProfitResult:
    """Full profit calculation for a MacBid -> resale arbitrage opportunity."""
    cost = calculate_macbid_cost(winning_bid, tax_rate)

    if platform == "ebay":
        revenue = calculate_ebay_revenue(sell_price, shipping_cost)
    elif platform == "amazon":
        revenue = calculate_amazon_revenue(sell_price, category, use_fba, is_large, shipping_cost)
    elif platform == "facebook":
        # Facebook Marketplace: no platform fees
        revenue = RevenueBreakdown(
            sell_price=sell_price,
            platform_fees=0.0,
            shipping_cost=shipping_cost,
            net_revenue=round(sell_price - shipping_cost, 2),
        )
    else:
        raise ValueError(f"Unknown platform: {platform}")

    profit = round(revenue.net_revenue - cost.total_cost, 2)
    roi_pct = round((profit / cost.total_cost) * 100, 2) if cost.total_cost > 0 else 0.0

    return ProfitResult(
        cost=cost,
        revenue=revenue,
        profit=profit,
        roi_pct=roi_pct,
    )
