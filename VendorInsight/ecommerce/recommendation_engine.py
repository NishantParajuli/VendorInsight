from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from .models import Product, UserInteraction, User
import numpy as np
from django.db.models import Case, When, Value, IntegerField


def get_product_features():
    products = Product.objects.all()
    features = []
    for product in products:
        # Combine textual data and normalize price
        feature = f"{product.name} {product.description} {product.categories.all()} {product.average_sentiment()}"
        features.append(feature)
    return features, [product.id for product in products]


def get_user_product_matrix():
    users = User.objects.all()
    products = Product.objects.all()

    user_product_matrix = np.zeros((users.count(), products.count()))

    for i, user in enumerate(users):
        user_interactions = UserInteraction.objects.filter(user=user)
        for interaction in user_interactions:
            product_index = list(products).index(interaction.product)
            interaction_weight = {'view': 1, 'wishlist': 2,
                                  'purchase': 3}[interaction.interaction_type]
            user_product_matrix[i, product_index] = interaction_weight

    return user_product_matrix, users, products


def recommend_products_content_based(product_id, num_recommendations=5):
    features, product_ids = get_product_features()
    vectorizer = TfidfVectorizer(stop_words='english')
    feature_matrix = vectorizer.fit_transform(features)
    product_idx = product_ids.index(product_id)
    cosine_similarities = cosine_similarity(
        feature_matrix[product_idx:product_idx+1], feature_matrix).flatten()
    related_product_indices = cosine_similarities.argsort(
    )[-num_recommendations-1:-1][::-1]  # Get indices of products sorted by similarity (largest first), excluding the top one (the product itself)

    # Exclude the product itself
    recommended_product_ids = [product_ids[i]
                               for i in related_product_indices if i != product_idx]
    return Product.objects.filter(id__in=recommended_product_ids)


def recommend_products(user_id, num_recommendations=5):
    content_based_recommendations = recommend_products_content_based(
        user_id, num_recommendations)

    user_product_matrix, users, products = get_user_product_matrix()
    user_index = list(users).index(User.objects.get(id=user_id))

    user_similarities = cosine_similarity(user_product_matrix)
    similar_users_indices = user_similarities[user_index].argsort()[
        ::-1][1:num_recommendations+1]

    similar_users_product_scores = user_product_matrix[similar_users_indices].sum(
        axis=0)
    top_product_indices = similar_users_product_scores.argsort()[
        ::-1][:num_recommendations]

    collaborative_recommendations = [products[i]
                                     for i in top_product_indices.tolist()]

    combined_recommendations = list(
        content_based_recommendations) + list(collaborative_recommendations)
    combined_recommendations = list(dict.fromkeys(combined_recommendations))[
        :num_recommendations]

    return combined_recommendations
