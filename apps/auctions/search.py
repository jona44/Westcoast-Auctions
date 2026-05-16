import logging
from datetime import datetime

from django.conf import settings
from django.db.models import Case, When, Q
from django.utils import timezone

from .models import Listing

try:
    from meilisearch import Client
    from meilisearch.errors import MeiliSearchApiError
except ImportError:
    Client = None
    MeiliSearchApiError = Exception

logger = logging.getLogger(__name__)
INDEX_NAME = getattr(settings, 'MEILISEARCH_INDEX', 'listings')


def get_meilisearch_client():
    if not Client:
        return None
    if not settings.MEILISEARCH_URL or not settings.MEILISEARCH_MASTER_KEY:
        return None
    try:
        return Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_MASTER_KEY)
    except Exception as exc:
        logger.warning('MeiliSearch client init failed: %s', exc)
        return None


def get_listing_index():
    client = get_meilisearch_client()
    if not client:
        return None

    try:
        return client.get_index(INDEX_NAME)
    except MeiliSearchApiError:
        try:
            return client.create_index(INDEX_NAME, {'primaryKey': 'id'})
        except Exception as exc:
            logger.warning('Unable to create MeiliSearch index: %s', exc)
            return None
    except Exception as exc:
        logger.warning('MeiliSearch get_index failed: %s', exc)
        return None


def listing_document(listing):
    return {
        'id': listing.id,
        'title': listing.title,
        'description': listing.description,
        'category': listing.get_category_display(),
        'seller_name': listing.seller.username,
        'is_active': listing.is_active,
        'created_at': listing.created_at.isoformat(),
    }


def index_listing(listing):
    index = get_listing_index()
    if not index:
        return
    if not listing.is_active:
        remove_listing_from_index(listing.id)
        return
    try:
        index.add_documents([listing_document(listing)])
    except Exception as exc:
        logger.warning('MeiliSearch index add failed: %s', exc)


def remove_listing_from_index(listing_id):
    index = get_listing_index()
    if not index:
        return
    try:
        index.delete_document(str(listing_id))
    except Exception as exc:
        logger.warning('MeiliSearch remove document failed: %s', exc)


def search_listings(query, limit=20):
    if not query:
        return Listing.objects.filter(is_active=True, end_time__gt=timezone.now()).order_by('-created_at')[:limit]

    index = get_listing_index()
    if index:
        try:
            response = index.search(query, {
                'limit': limit,
                'attributesToRetrieve': ['id', 'title', 'description', 'category'],
                'attributesToHighlight': ['title', 'description'],
            })
            ids = [int(hit['id']) for hit in response.get('hits', []) if hit.get('id')]
            if ids:
                preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ids)])
                return Listing.objects.filter(pk__in=ids, is_active=True, end_time__gt=timezone.now()).order_by(preserved)
            return Listing.objects.filter(is_active=True, end_time__gt=timezone.now()).none()
        except Exception as exc:
            logger.warning('MeiliSearch search failed: %s', exc)

    return Listing.objects.filter(
        is_active=True,
        end_time__gt=timezone.now()
    ).filter(
        Q(title__icontains=query)
        | Q(description__icontains=query)
        | Q(category__icontains=query)
    ).order_by('-created_at')[:limit]


def search_suggestions(query, limit=6):
    return search_listings(query, limit=limit)
