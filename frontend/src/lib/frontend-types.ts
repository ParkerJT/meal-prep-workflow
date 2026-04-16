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

export interface SavedRecipeResponse {
  id: string;
  recipe_id: string;
  saved_at: string;
  notes: string;
  converted_recipe: ConvertedRecipe | null;
  published: boolean;
  copied_from_user_id: string | null;
  copied_from_saved_recipe_id: string | null;
}

export interface PublishedRecipeSummary {
  owner_user_id: string;
  saved_recipe_id: string;
  saved_at: string;
  converted_recipe: ConvertedRecipe | null;
}

export interface PublishedRecipeDetail extends PublishedRecipeSummary {
  recipe_id: string;
}

export interface PaginatedPublishedResponse {
  items: PublishedRecipeSummary[];
  next_cursor: string | null;
}
