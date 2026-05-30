export interface ConvertedRecipe {
  title: string;
  description?: string | null;
  servings: number;
  ingredients: Array<{ name: string; quantity: number | string; unit?: string | null }>;
  instructions: string[];
  nutritional_info: {
    calories: number;
    protein: number;
  };
  conversion_metadata: {
    original_recipe_url: string;
    conversion_notes: string;
  };
}

export interface OriginalRecipe {
  title: string;
  description?: string | null;
  servings: number;
  ingredients: Array<{ name: string; quantity: number | string; unit?: string | null }>;
  instructions: string[];
}

export interface GenerateResponse {
  original_recipe: OriginalRecipe;
  converted_recipe: ConvertedRecipe;
  source_url: string | null;
  source_type: "web" | "youtube" | "text";
}

export interface SavedRecipeResponse {
  id: string;
  saved_at: string;
  notes: string;
  source_url: string | null;
  source_type: "web" | "youtube" | "text" | null;
  original_recipe: OriginalRecipe | null;
  converted_recipe: ConvertedRecipe | null;
}

export type SubscriptionStatus = "active" | "trialing" | "past_due" | "canceled" | "none";
export type SubscriptionPlan = "monthly" | "annual";
export type SubscriptionSource = "app_trial" | "stripe";

export interface SubscriptionStatusResponse {
  status: SubscriptionStatus;
  plan: SubscriptionPlan | null;
  current_period_end: string | null;
  trial_end: string | null;
  trial_started_at?: string | null;
  source?: SubscriptionSource | null;
  /** True when the user has a Stripe Customer ID (billing portal can open). */
  billing_portal_available?: boolean;
}
