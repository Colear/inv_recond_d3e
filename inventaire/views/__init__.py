from .auth import (
    CustomLoginView,
    CustomLogoutView,
)

from .home import (
    HomePageView,
)

from .stock import (
    InventaireListView,
    imprimer_planche_etiquettes,
    search_by_inv,
)

from .workflow import (
    NouveauMaterielView,
    ajax_create_marque,
    modifier_materiel,
)

from .dons import (
    faire_un_don,
    generer_fiche_don_pdf,
)

from .rapports import (
    rapport_activite_pdf,
)