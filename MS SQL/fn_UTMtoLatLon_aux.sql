USE [id_banco]
GO

CREATE FUNCTION [SCHEMA].[fn_UTMtoLatLon_aux]
(
    @x FLOAT,
    @y FLOAT,
    @zone INT,
    @southHem BIT
)
RETURNS TABLE
AS
RETURN
(
    WITH Resultado_Puro AS (
        -- Primeiro, chama a função original - fn_UTMtoLatLon (não calibrada)
        SELECT * FROM TERRAS.fn_UTMtoLatLon(@x, @y, @zone, @southHem)
    ),
    Coeficientes_Correcao AS (
        -- *** COPIE E COLE OS 6 COEFICIENTES AQUI ***
        SELECT
            CAST(-0.000311338159541348 AS FLOAT) AS a_lat,
            CAST(1.58413908553208E-10 AS FLOAT) AS b_lat,
            CAST(3.15225255775211E-11 AS FLOAT) AS c_lat,

            CAST(-1.02999564448405E-07 AS FLOAT) AS a_lon,
            CAST(-1.73997842401354E-20 AS FLOAT) AS b_lon,
            CAST(-5.7582410969698E-20 AS FLOAT) AS c_lon
    ),
    Resultado_Calibrado AS (
        -- Aplica a fórmula de correção: Resultado_Final = Resultado_Bruto + (a + b*X + c*Y)
        SELECT
            r.Latitude  + (c.a_lat + c.b_lat * @x + c.c_lat * @y) AS Latitude,
            r.Longitude + (c.a_lon + c.b_lon * @x + c.c_lon * @y) AS Longitude
        FROM Resultado_Puro r CROSS JOIN Coeficientes_Correcao c
    )
    SELECT * FROM Resultado_Calibrado
);
GO


