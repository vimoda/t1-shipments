from __future__ import annotations

from .base import BaseResource
from ..models.tracking import Pickup, PickupRequest


class PickupsResource(BaseResource):
    def schedule_pickup(self, req: PickupRequest) -> Pickup:
        url = self._endpoints.url(self._endpoints.pickup)
        payload: dict = {
            "mensajeria": req.carrier,
            "nombre_contacto": req.contact_first_name,
            "apellidos_contacto": req.contact_last_name,
            "email": req.email,
            "calle": req.street,
            "numero": req.number,
            "colonia": req.neighborhood,
            "telefono": req.phone,
            "estado": req.state,
            "municipio": req.municipality,
            "codigo_postal": req.postal_code,
            "referencias": req.references,
            "cantidad_piezas": req.pieces,
            "peso": req.weight,
            "largo": req.length,
            "ancho": req.width,
            "alto": req.height,
            "fecha": req.date,
            "hora_inicio": req.open_time,
            "horario_cierre": req.close_time,
        }
        if self._shop_id:
            payload["comercio_id"] = self._shop_id

        data = self.request("POST", url, json=payload)

        if not isinstance(data, dict):
            raise ValueError(f"Expected dict response, got {type(data)}")
        if data.get("success") is False:
            raise ValueError(f"API error: {data.get('message', 'Unknown error')}")
        
        recoleccion = data["detail"]["recoleccion"]
        
        return Pickup(
            pickup_id=recoleccion["pick_up"],
            location=recoleccion["location"],
            localization=recoleccion["localizacion"],
            status=recoleccion["status"],
            message=recoleccion["mensaje"],
        )
