USE [id_banco];
GO

IF OBJECT_ID('[SCHEMA].[nomeVWouTb]', 'V') IS NOT NULL
    DROP VIEW [SCHEMA].[nomeVWouTb];
GO

CREATE VIEW [SCHEMA].[nomeVWouTb]
AS
WITH Fonte_Valida AS (
    SELECT
        qgs_fid,
        IDTERRENO,
        CAMPO_GEOM.MakeValid().STCentroid() AS Centroide
    FROM
        [TERRAS].[TbOrigemDados] 
    WHERE
        CAMPO_GEOM IS NOT NULL AND CAMPO_GEOM.STIsEmpty() = 0
)
SELECT
    t.ID,
    convertido.Latitude AS Centroide_Latitude,
    convertido.Longitude AS Centroide_Longitude,
    'POINT (' + ISNULL(CAST(convertido.Longitude AS VARCHAR(50)), '') 
              + ' ' + ISNULL(CAST(convertido.Latitude AS VARCHAR(50)), '') 
              + ')' AS Centroide_LatLon_WKT

FROM
    Fonte_Valida AS t
    OUTER APPLY TERRAS.fn_UTMtoLatLon_Calibrada(
        t.Centroide.STX,
        t.Centroide.STY,
        23, -- Zona UTM
        1  -- Hemisfério Sul
    ) AS convertido;
GO
