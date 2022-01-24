<?xml version="1.0"?>

<xsl:stylesheet
    version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:_alto="http://www.loc.gov/standards/alto/ns-v3#">

  <xsl:output method="text"/>
  <xsl:strip-space elements="*" />

  <!--
      A bit fugley, but last() doesn't work for the "omit last comma"
      trick when you use separate templates cuz of "grouping scope"
  -->
  <xsl:template match="/">
  {"layout":
    {"pages": [
    <xsl:for-each select="_alto:alto/_alto:Layout/_alto:Page">
      {<xsl:call-template name="output_bb_dims_attrs"/>,
      "printspaces": [
      <xsl:for-each select="_alto:PrintSpace">
        {<xsl:call-template name="output_bb_dims_attrs"/>,
        <xsl:call-template name="output_bb_location_attrs"/>,
        "comp_blocks": [
        <xsl:for-each select="_alto:ComposedBlock">
          {<xsl:call-template name="output_bb_dims_attrs"/>,
          <xsl:call-template name="output_bb_location_attrs"/>,
          "text_block": [
          <xsl:for-each select="_alto:TextBlock">
            {<xsl:call-template name="output_bb_dims_attrs"/>,
            <xsl:call-template name="output_bb_location_attrs"/>,
            "text_lines": [
            <xsl:for-each select="_alto:TextLine">
              {<xsl:call-template name="output_bb_dims_attrs"/>,
              <xsl:call-template name="output_bb_location_attrs"/>,
              "token_seq": [
              <xsl:for-each select="_alto:String|_alto:SP">
                <xsl:choose>
                  <xsl:when test="local-name() = 'String'">
                    {"type": "String",
                    <xsl:call-template name="output_bb_dims_attrs"/>,
                    <xsl:call-template name="output_bb_location_attrs"/>,
                    <xsl:call-template name="output_text_attrs"/>
                    }<xsl:if test="position()!=last()">,</xsl:if>
                  </xsl:when>
                  <xsl:otherwise> <!-- Could collapse in to String node? -->
                    {"type": "Sep",
                    "width":<xsl:value-of select="@WIDTH"/>, <!-- bodge -->
                    <xsl:call-template name="output_bb_location_attrs"/>
                    }<xsl:if test="position()!=last()">,</xsl:if>
                  </xsl:otherwise>
                </xsl:choose>
              </xsl:for-each>
              ]}<xsl:if test="position()!=last()">,</xsl:if>
            </xsl:for-each>
            ]}<xsl:if test="position()!=last()">,</xsl:if>
          </xsl:for-each>
          ]}<xsl:if test="position()!=last()">,</xsl:if>
        </xsl:for-each>
        ]}<xsl:if test="position()!=last()">,</xsl:if>
      </xsl:for-each>
      ]}<xsl:if test="position()!=last()">,</xsl:if>
    </xsl:for-each>
  ]}}
  </xsl:template>

  <xsl:template name="output_text_attrs">
    "wc": <xsl:value-of select="@WC"/>,
    "content": "<xsl:value-of select="@CONTENT"/>"
  </xsl:template>
  
  <xsl:template name="output_bb_location_attrs">
    "hpos": <xsl:value-of select="@HPOS"/>,
    "vpos": <xsl:value-of select="@VPOS"/>
  </xsl:template>
  
  <xsl:template name="output_bb_dims_attrs">
    "width":<xsl:value-of select="@WIDTH"/>,
    "height":<xsl:value-of select="@HEIGHT"/>
  </xsl:template>
</xsl:stylesheet>
